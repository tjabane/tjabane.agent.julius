from fastapi.testclient import TestClient

from julius_application.api import app


def test_ping_returns_ok(monkeypatch):
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")

    with TestClient(app) as client:
        response = client.get("/ping")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_returns_503_when_unhealthy(monkeypatch):
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    monkeypatch.setattr(
        "julius_application.api.run_health_checks",
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
