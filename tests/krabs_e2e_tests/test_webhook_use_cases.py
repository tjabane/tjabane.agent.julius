import pytest
from fastapi.testclient import TestClient

from krabs_application.fastapi_app import app
from krabs_application.http_routes import get_agent_runner, get_message_sender

pytestmark = pytest.mark.e2e


class RecordingMessageSender:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, str]] = []

    def send_message(self, to: str, body: str) -> None:
        self.sent_messages.append({"to": to, "body": body})


class UseCaseAgentRunner:
    def __init__(self) -> None:
        self.requests: list[dict[str, str]] = []

    def __call__(self, whatsapp_number: str, user_message: str) -> str:
        self.requests.append({"whatsapp_number": whatsapp_number, "user_message": user_message})
        message = user_message.lower()
        if "available" in message or "balance" in message:
            return "Aye, available balance: R12,345. Current balance: R12,890."
        if "transactions" in message or "last week" in message:
            return "Last week: R3,860 spent. Pending transactions included."
        if message.startswith("pay "):
            return "Confirm before I pay R8,500 to Rent from cheque."
        if message.startswith("move "):
            return "Confirm before I transfer R2,000 from savings to cheque."
        if "statements" in message or "tax certificates" in message:
            return "Statements found for the requested period."
        if "scoreboard" in message:
            return "SPENDING SCOREBOARD\nScore: 78/100\nSpent: R3,860\nWatch List: dining."
        if "separate groceries" in message:
            return "Saved preference: separate groceries from restaurants."
        if "use this format" in message:
            return "Saved skill for monthly spending reviews."
        return "Aye, request handled."


@pytest.fixture
def e2e_harness():
    sender = RecordingMessageSender()
    runner = UseCaseAgentRunner()
    app.dependency_overrides[get_message_sender] = lambda: sender
    app.dependency_overrides[get_agent_runner] = lambda: runner
    try:
        with TestClient(app) as client:
            yield client, sender, runner
    finally:
        app.dependency_overrides.clear()


def _post_whatsapp_message(client: TestClient, body: str):
    return client.post(
        "/webhook",
        data={"From": "whatsapp:+27123456789", "Body": body},
    )


def _last_reply(sender: RecordingMessageSender) -> str:
    return sender.sent_messages[-1]["body"]


def test_balance_use_case_returns_available_balance(e2e_harness):
    client, sender, runner = e2e_harness

    response = _post_whatsapp_message(client, "How much is available in my cheque account?")

    assert response.status_code == 200
    assert runner.requests == [
        {
            "whatsapp_number": "+27123456789",
            "user_message": "How much is available in my cheque account?",
        }
    ]
    assert sender.sent_messages[-1]["to"] == "+27123456789"
    assert "available balance" in _last_reply(sender).lower()


def test_recent_spending_use_case_includes_pending_transactions(e2e_harness):
    client, sender, _runner = e2e_harness

    response = _post_whatsapp_message(client, "Show me my card transactions from last week, including pending ones.")

    assert response.status_code == 200
    reply = _last_reply(sender).lower()
    assert "last week" in reply
    assert "pending" in reply


def test_beneficiary_payment_use_case_requires_confirmation(e2e_harness):
    client, sender, _runner = e2e_harness

    response = _post_whatsapp_message(client, "Pay R8,500 to Rent from my cheque account.")

    assert response.status_code == 200
    reply = _last_reply(sender).lower()
    assert "confirm" in reply
    assert "pay" in reply


def test_own_account_transfer_use_case_requires_confirmation(e2e_harness):
    client, sender, _runner = e2e_harness

    response = _post_whatsapp_message(client, "Move R2,000 from savings to cheque.")

    assert response.status_code == 200
    reply = _last_reply(sender).lower()
    assert "confirm" in reply
    assert "transfer" in reply


def test_documents_use_case_returns_document_availability(e2e_harness):
    client, sender, _runner = e2e_harness

    response = _post_whatsapp_message(client, "Find my statements for the last three months.")

    assert response.status_code == 200
    assert "statements found" in _last_reply(sender).lower()


def test_spending_scoreboard_use_case_returns_scoreboard(e2e_harness):
    client, sender, _runner = e2e_harness

    response = _post_whatsapp_message(client, "Show me my weekly spending scoreboard.")

    assert response.status_code == 200
    reply = _last_reply(sender).lower()
    assert "spending scoreboard" in reply
    assert "score" in reply
    assert "watch list" in reply


def test_memory_preference_use_case_saves_preference(e2e_harness):
    client, sender, _runner = e2e_harness

    response = _post_whatsapp_message(client, "When you report spending, separate groceries from restaurants.")

    assert response.status_code == 200
    assert "saved preference" in _last_reply(sender).lower()


def test_skill_reuse_use_case_saves_reusable_report_skill(e2e_harness):
    client, sender, _runner = e2e_harness

    response = _post_whatsapp_message(client, "Use this format for my monthly spending reviews from now on.")

    assert response.status_code == 200
    assert "saved skill" in _last_reply(sender).lower()


def test_health_use_case_exposes_liveness_and_dependency_status(e2e_harness, monkeypatch):
    client, _sender, _runner = e2e_harness
    monkeypatch.setattr(
        "krabs_application.http_routes.run_health_checks",
        lambda: {"status": "healthy", "dependencies": {}},
    )

    ping_response = client.get("/ping")
    health_response = client.get("/health")

    assert ping_response.status_code == 200
    assert ping_response.json()["status"] == "ok"
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "healthy"
