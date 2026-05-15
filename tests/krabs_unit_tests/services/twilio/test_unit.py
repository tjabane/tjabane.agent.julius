from unittest.mock import MagicMock, patch, call
import pytest
from krabs_services.communication.twilio_client import TwilioClient


@pytest.fixture(autouse=True)
def twilio_env(monkeypatch):
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "test-account-sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "test-auth-token")
    monkeypatch.setenv("TWILIO_WHATSAPP_NUMBER", "+27821234567")


# ── Initialisation ────────────────────────────────────────────────────────────

class TestInit:
    @patch("krabs_services.communication.twilio_client.Client")
    def test_creates_twilio_client_with_credentials(self, mock_client_cls):
        TwilioClient()
        mock_client_cls.assert_called_once_with("test-account-sid", "test-auth-token")

    @patch("krabs_services.communication.twilio_client.Client")
    def test_stores_from_number(self, mock_client_cls):
        client = TwilioClient()
        assert client._from_number == "+27821234567"


# ── send_message ──────────────────────────────────────────────────────────────

class TestSendMessage:
    @patch("krabs_services.communication.twilio_client.Client")
    def test_sends_message_with_whatsapp_prefix(self, mock_client_cls):
        mock_twilio = MagicMock()
        mock_client_cls.return_value = mock_twilio

        client = TwilioClient()
        client.send_message(to="+27829876543", body="Hello!")

        mock_twilio.messages.create.assert_called_once_with(
            from_="whatsapp:+27821234567",
            to="whatsapp:+27829876543",
            body="Hello!",
        )

    @patch("krabs_services.communication.twilio_client.Client")
    def test_from_number_has_whatsapp_prefix(self, mock_client_cls):
        mock_twilio = MagicMock()
        mock_client_cls.return_value = mock_twilio

        client = TwilioClient()
        client.send_message(to="+27829876543", body="Test")

        call_kwargs = mock_twilio.messages.create.call_args.kwargs
        assert call_kwargs["from_"].startswith("whatsapp:")

    @patch("krabs_services.communication.twilio_client.Client")
    def test_to_number_has_whatsapp_prefix(self, mock_client_cls):
        mock_twilio = MagicMock()
        mock_client_cls.return_value = mock_twilio

        client = TwilioClient()
        client.send_message(to="+27829876543", body="Test")

        call_kwargs = mock_twilio.messages.create.call_args.kwargs
        assert call_kwargs["to"].startswith("whatsapp:")

    @patch("krabs_services.communication.twilio_client.Client")
    def test_sends_correct_body(self, mock_client_cls):
        mock_twilio = MagicMock()
        mock_client_cls.return_value = mock_twilio

        client = TwilioClient()
        client.send_message(to="+27829876543", body="Your balance is R1,000")

        call_kwargs = mock_twilio.messages.create.call_args.kwargs
        assert call_kwargs["body"] == "Your balance is R1,000"


# ── parse_webhook ─────────────────────────────────────────────────────────────

class TestParseWebhook:
    def test_extracts_number_and_body(self):
        form_data = {"From": "whatsapp:+27829876543", "Body": "Show my balance"}
        number, body = TwilioClient.parse_webhook(form_data)

        assert number == "+27829876543"
        assert body == "Show my balance"

    def test_strips_whatsapp_prefix_from_number(self):
        form_data = {"From": "whatsapp:+27829876543", "Body": "Hello"}
        number, _ = TwilioClient.parse_webhook(form_data)

        assert not number.startswith("whatsapp:")

    def test_returns_empty_strings_for_missing_fields(self):
        number, body = TwilioClient.parse_webhook({})

        assert number == ""
        assert body == ""

    def test_handles_missing_from_field(self):
        form_data = {"Body": "Hello"}
        number, body = TwilioClient.parse_webhook(form_data)

        assert number == ""
        assert body == "Hello"

    def test_handles_missing_body_field(self):
        form_data = {"From": "whatsapp:+27829876543"}
        number, body = TwilioClient.parse_webhook(form_data)

        assert number == "+27829876543"
        assert body == ""

    def test_handles_number_without_whatsapp_prefix(self):
        form_data = {"From": "+27829876543", "Body": "Hello"}
        number, _ = TwilioClient.parse_webhook(form_data)

        assert number == "+27829876543"

    def test_is_static_method(self):
        TwilioClient.parse_webhook({"From": "whatsapp:+1234567890", "Body": "test"})
