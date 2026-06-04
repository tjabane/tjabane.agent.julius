from unittest.mock import MagicMock, patch

import pytest

from krabs_services.communication.email_service import AzureEmailService


@pytest.fixture(autouse=True)
def email_env(monkeypatch):
    monkeypatch.setenv("AZURE_COMMUNICATION_CONNECTION_STRING", "endpoint=https://test.communication.azure.com/;accesskey=dGVzdA==")
    monkeypatch.setenv("EMAIL_SENDER_ADDRESS", "DoNotReply@test.azurecomm.net")
    monkeypatch.setenv("EMAIL_RECIPIENT_ADDRESS", "user@example.com")


# ── Initialisation ────────────────────────────────────────────────────────────

class TestInit:
    @patch("krabs_services.communication.email_service.EmailClient")
    def test_creates_client_from_connection_string(self, mock_client_cls):
        AzureEmailService()
        mock_client_cls.from_connection_string.assert_called_once_with(
            "endpoint=https://test.communication.azure.com/;accesskey=dGVzdA=="
        )

    @patch("krabs_services.communication.email_service.EmailClient")
    def test_stores_sender_address(self, mock_client_cls):
        service = AzureEmailService()
        assert service._sender == "DoNotReply@test.azurecomm.net"

    @patch("krabs_services.communication.email_service.EmailClient")
    def test_stores_recipient_address(self, mock_client_cls):
        service = AzureEmailService()
        assert service._recipient == "user@example.com"


# ── send_report ───────────────────────────────────────────────────────────────

class TestSendReport:
    @patch("krabs_services.communication.email_service.EmailClient")
    def test_calls_begin_send(self, mock_client_cls):
        mock_acs = MagicMock()
        mock_client_cls.from_connection_string.return_value = mock_acs

        service = AzureEmailService()
        service.send_report(subject="Weekly Report", body="Here is your report.")

        mock_acs.begin_send.assert_called_once()

    @patch("krabs_services.communication.email_service.EmailClient")
    def test_message_has_correct_sender(self, mock_client_cls):
        mock_acs = MagicMock()
        mock_client_cls.from_connection_string.return_value = mock_acs

        service = AzureEmailService()
        service.send_report(subject="Report", body="Body")

        message = mock_acs.begin_send.call_args.args[0]
        assert message["senderAddress"] == "DoNotReply@test.azurecomm.net"

    @patch("krabs_services.communication.email_service.EmailClient")
    def test_message_has_correct_recipient(self, mock_client_cls):
        mock_acs = MagicMock()
        mock_client_cls.from_connection_string.return_value = mock_acs

        service = AzureEmailService()
        service.send_report(subject="Report", body="Body")

        message = mock_acs.begin_send.call_args.args[0]
        assert message["recipients"]["to"][0]["address"] == "user@example.com"

    @patch("krabs_services.communication.email_service.EmailClient")
    def test_message_has_correct_subject(self, mock_client_cls):
        mock_acs = MagicMock()
        mock_client_cls.from_connection_string.return_value = mock_acs

        service = AzureEmailService()
        service.send_report(subject="Weekly Report", body="Body")

        message = mock_acs.begin_send.call_args.args[0]
        assert message["content"]["subject"] == "Weekly Report"

    @patch("krabs_services.communication.email_service.EmailClient")
    def test_message_has_correct_body(self, mock_client_cls):
        mock_acs = MagicMock()
        mock_client_cls.from_connection_string.return_value = mock_acs

        service = AzureEmailService()
        service.send_report(subject="Report", body="Here is your weekly summary.")

        message = mock_acs.begin_send.call_args.args[0]
        assert message["content"]["plainText"] == "Here is your weekly summary."

    @patch("krabs_services.communication.email_service.EmailClient")
    def test_waits_for_send_to_complete(self, mock_client_cls):
        mock_acs = MagicMock()
        mock_client_cls.from_connection_string.return_value = mock_acs

        service = AzureEmailService()
        service.send_report(subject="Report", body="Body")

        mock_acs.begin_send.return_value.result.assert_called_once()
