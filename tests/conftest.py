import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(autouse=True)
def dummy_env(monkeypatch, request):
    """Provide dummy env vars for unit tests. Integration tests use real .env values."""
    if request.node.get_closest_marker("integration"):
        return
    monkeypatch.setenv("INVESTEC_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("INVESTEC_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("INVESTEC_API_KEY", "test-api-key")
    monkeypatch.setenv("INVESTEC_SANDBOX", "true")
    monkeypatch.setenv("INVESTEC_URL", "https://openapisandbox.investec.com")
    monkeypatch.setenv("INVESTEC_TIMEOUT_SECONDS", "5.0")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv(
        "COSMOS_CONNECTION_STRING", "AccountEndpoint=https://fake.documents.azure.com:443/;AccountKey=ZmFrZWtleWZha2U=;"
    )
    monkeypatch.setenv("COSMOS_DATABASE", "krabs")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACtest")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "testtoken")
    monkeypatch.setenv("TWILIO_WHATSAPP_NUMBER", "+15005550006")
    monkeypatch.setenv(
        "AZURE_COMMUNICATION_CONNECTION_STRING", "endpoint=https://fake.communication.azure.com;accesskey=ZmFrZQ=="
    )
    monkeypatch.setenv("EMAIL_SENDER_ADDRESS", "sender@test.com")
    monkeypatch.setenv("EMAIL_RECIPIENT_ADDRESS", "recipient@test.com")
