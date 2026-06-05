import os
import uuid
from urllib.parse import urlparse

import httpx
import pytest
from fastapi.testclient import TestClient

from krabs_application.fastapi_app import app
from krabs_application.http_routes import get_message_sender

pytestmark = pytest.mark.e2e_live

_REQUIRED_ENV = (
    "OPENAI_API_KEY",
    "INVESTEC_CLIENT_ID",
    "INVESTEC_CLIENT_SECRET",
    "INVESTEC_API_KEY",
    "INVESTEC_URL",
    "INVESTEC_TIMEOUT_SECONDS",
    "COSMOS_CONNECTION_STRING",
    "COSMOS_DATABASE",
    "AZURE_COMMUNICATION_CONNECTION_STRING",
    "EMAIL_SENDER_ADDRESS",
    "EMAIL_RECIPIENT_ADDRESS",
)

_ALLOWED_DEVELOPMENT_INVESTEC_HOST = "openapisandbox.investec.com"


class RecordingMessageSender:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, str]] = []

    def send_message(self, to: str, body: str) -> None:
        self.sent_messages.append({"to": to, "body": body})


def _missing_live_env() -> list[str]:
    return [name for name in _REQUIRED_ENV if not os.environ.get(name)]


def _live_e2e_enabled() -> bool:
    return os.environ.get("KRABS_RUN_LIVE_E2E", "").lower() == "true"


def _cosmos_endpoint() -> str | None:
    connection_string = os.environ.get("COSMOS_CONNECTION_STRING", "")
    for part in connection_string.split(";"):
        if part.startswith("AccountEndpoint="):
            return part.removeprefix("AccountEndpoint=")
    return None


def _cosmos_endpoint_is_reachable() -> bool:
    endpoint = _cosmos_endpoint()
    if not endpoint:
        return False

    parsed = urlparse(endpoint)
    if parsed.hostname not in {"localhost", "127.0.0.1"}:
        return True

    try:
        httpx.get(endpoint, timeout=2.0)
    except httpx.RequestError:
        return False
    return True


@pytest.fixture(autouse=True)
def require_live_e2e_environment(monkeypatch):
    if not _live_e2e_enabled():
        pytest.skip("Set KRABS_RUN_LIVE_E2E=true to run live webhook E2E tests.")

    missing = _missing_live_env()
    if missing:
        pytest.skip(f"Missing live E2E environment variables: {', '.join(missing)}")

    if os.environ["OPENAI_API_KEY"] == "sk-test":
        pytest.skip("OPENAI_API_KEY must be a real key for live webhook E2E tests.")

    investec_host = urlparse(os.environ["INVESTEC_URL"]).hostname
    if investec_host != _ALLOWED_DEVELOPMENT_INVESTEC_HOST:
        pytest.skip("Live webhook E2E tests are sandbox-only. Set INVESTEC_URL to the Investec sandbox URL.")

    monkeypatch.setenv("OPENAI_MODEL", os.environ.get("OPENAI_E2E_MODEL", "gpt-4o-mini"))

    if not _cosmos_endpoint_is_reachable():
        pytest.skip("Cosmos DB endpoint is not reachable. Start the local emulator before live webhook E2E tests.")


@pytest.fixture
def live_webhook_harness():
    sender = RecordingMessageSender()
    app.dependency_overrides[get_message_sender] = lambda: sender
    try:
        with TestClient(app) as client:
            yield client, sender
    finally:
        app.dependency_overrides.clear()


def _unique_whatsapp_number() -> str:
    digits = str(uuid.uuid4().int)[-9:]
    return f"+27{digits}"


def _post_live_whatsapp_message(client: TestClient, body: str) -> tuple[str, object]:
    number = _unique_whatsapp_number()
    response = client.post(
        "/webhook",
        data={"From": f"whatsapp:{number}", "Body": body},
    )
    return number, response


def _assert_user_safe_reply(sender: RecordingMessageSender) -> str:
    assert sender.sent_messages, "Expected the webhook to send a reply."
    reply = sender.sent_messages[-1]["body"]
    assert reply.strip()
    unsafe_fragments = ("traceback", "httpx.", "openai.", "exception", "stack trace")
    assert not any(fragment in reply.lower() for fragment in unsafe_fragments)
    return reply


def test_live_webhook_can_answer_account_summary(live_webhook_harness):
    client, sender = live_webhook_harness

    number, response = _post_live_whatsapp_message(
        client,
        "List my Investec accounts. Keep the reply under 60 words.",
    )

    assert response.status_code == 200
    assert sender.sent_messages[-1]["to"] == number
    reply = _assert_user_safe_reply(sender)
    assert len(reply) <= 800


def test_live_webhook_can_generate_spending_scoreboard(live_webhook_harness):
    client, sender = live_webhook_harness

    number, response = _post_live_whatsapp_message(
        client,
        "Show me my weekly spending scoreboard. Keep it brief.",
    )

    assert response.status_code == 200
    assert sender.sent_messages[-1]["to"] == number
    reply = _assert_user_safe_reply(sender)
    assert "score" in reply.lower() or "spending" in reply.lower()


def test_live_webhook_payment_request_stops_for_confirmation(live_webhook_harness):
    client, sender = live_webhook_harness

    number, response = _post_live_whatsapp_message(
        client,
        "Pay R1 to a saved beneficiary named Test from my cheque account.",
    )

    assert response.status_code == 200
    assert sender.sent_messages[-1]["to"] == number
    reply = _assert_user_safe_reply(sender).lower()
    assert "confirm" in reply or "confirmation" in reply
