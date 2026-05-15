from fastapi.testclient import TestClient

from krabs_application.fastapi_app import app
from krabs_application.http_routes import get_message_sender


class StubMessageSender:
    def __init__(self):
        self.sent_messages = []

    def send_message(self, to: str, body: str) -> None:
        self.sent_messages.append({"to": to, "body": body})


def test_ping_returns_ok(monkeypatch):
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")

    with TestClient(app) as client:
        response = client.get("/ping")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_returns_503_when_unhealthy(monkeypatch):
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    monkeypatch.setattr(
        "krabs_application.http_routes.run_health_checks",
        lambda: {"status": "unhealthy", "dependencies": {}},
    )

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "unhealthy"


def test_webhook_rejects_missing_twilio_form(monkeypatch):
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")

    with TestClient(app) as client:
        response = client.post("/webhook", data={})

    assert response.status_code == 400


def test_legacy_api_webhook_alias(monkeypatch):
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")

    with TestClient(app) as client:
        response = client.post("/api/webhook", data={})

    assert response.status_code == 400


def test_webhook_uses_injected_message_sender(monkeypatch):
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
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
