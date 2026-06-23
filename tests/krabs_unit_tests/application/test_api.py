from fastapi.testclient import TestClient

from krabs_application.fastapi_app import app
from krabs_application.http_routes import get_message_sender
from krabs_observability import current_turn_context


class StubMessageSender:
    def __init__(self):
        self.sent_messages = []

    def send_message(self, to: str, body: str) -> None:
        self.sent_messages.append({"to": to, "body": body})


def test_ping_returns_ok():
    with TestClient(app) as client:
        response = client.get("/ping")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_returns_503_when_unhealthy(monkeypatch):
    monkeypatch.setattr(
        "krabs_application.http_routes.run_health_checks",
        lambda: {"status": "unhealthy", "dependencies": {}},
    )

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "unhealthy"


def test_webhook_rejects_missing_twilio_form():
    with TestClient(app) as client:
        response = client.post("/webhook", data={})

    assert response.status_code == 400


def test_legacy_api_webhook_alias():
    with TestClient(app) as client:
        response = client.post("/api/webhook", data={})

    assert response.status_code == 400


def test_webhook_uses_injected_message_sender(monkeypatch):
    sender = StubMessageSender()
    app.dependency_overrides[get_message_sender] = lambda: sender
    monkeypatch.setattr(
        "krabs_application.http_routes.run",
        lambda whatsapp_number, user_message: f"reply to {user_message}",
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/webhook",
                data={"From": "whatsapp:+27829876543", "Body": "balance"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert sender.sent_messages == [{"to": "+27829876543", "body": "reply to balance"}]


def test_webhook_records_bounded_request_metric_without_payload(monkeypatch):
    sender = StubMessageSender()
    app.dependency_overrides[get_message_sender] = lambda: sender
    recorded_metrics = []
    monkeypatch.setattr(
        "krabs_application.http_routes.run",
        lambda whatsapp_number, user_message: f"reply to {user_message}",
    )
    monkeypatch.setattr(
        "krabs_application.http_routes.record_request_metric",
        lambda **kwargs: recorded_metrics.append(kwargs),
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/webhook",
                data={"From": "whatsapp:+27829876543", "Body": "private balance question"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert recorded_metrics[0]["route"] == "/webhook"
    assert recorded_metrics[0]["status"] == "success"
    assert recorded_metrics[0]["http_status_code"] == 200
    assert "+27829876543" not in str(recorded_metrics)
    assert "private balance question" not in str(recorded_metrics)


def test_webhook_records_error_metric_for_bad_request(monkeypatch):
    recorded_metrics = []
    monkeypatch.setattr(
        "krabs_application.http_routes.record_request_metric",
        lambda **kwargs: recorded_metrics.append(kwargs),
    )

    with TestClient(app) as client:
        response = client.post("/webhook", data={})

    assert response.status_code == 400
    assert recorded_metrics[0]["route"] == "/webhook"
    assert recorded_metrics[0]["status"] == "error"
    assert recorded_metrics[0]["http_status_code"] == 400


def test_webhook_records_error_metric_for_agent_failure(monkeypatch):
    sender = StubMessageSender()
    app.dependency_overrides[get_message_sender] = lambda: sender
    recorded_metrics = []

    def failing_run(whatsapp_number, user_message):
        raise RuntimeError("agent failed")

    monkeypatch.setattr("krabs_application.http_routes.run", failing_run)
    monkeypatch.setattr(
        "krabs_application.http_routes.record_request_metric",
        lambda **kwargs: recorded_metrics.append(kwargs),
    )

    try:
        try:
            with TestClient(app) as client:
                client.post(
                    "/webhook",
                    data={"From": "whatsapp:+27829876543", "Body": "balance"},
                )
        except RuntimeError:
            pass
    finally:
        app.dependency_overrides.clear()

    assert recorded_metrics[0]["route"] == "/webhook"
    assert recorded_metrics[0]["status"] == "error"
    assert recorded_metrics[0]["http_status_code"] == 500


def test_webhook_sets_turn_context_for_agent_thread(monkeypatch):
    sender = StubMessageSender()
    observed_context = {}
    app.dependency_overrides[get_message_sender] = lambda: sender

    def fake_run(whatsapp_number, user_message):
        observed_context["turn_context"] = current_turn_context()
        return f"reply to {user_message}"

    monkeypatch.setattr("krabs_application.http_routes.run", fake_run)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/webhook",
                data={"From": "whatsapp:+27829876543", "Body": "balance"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert observed_context["turn_context"] is not None
    assert observed_context["turn_context"].turn_id
    assert observed_context["turn_context"].session_id.startswith("wa_")
    assert "+27829876543" not in observed_context["turn_context"].session_id
