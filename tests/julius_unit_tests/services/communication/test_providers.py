from julius_services.communication.email_service import InMemoryEmailService
from julius_services.communication.providers import (
    get_message_sender,
    get_report_sender,
    reset_communication_providers,
)
from julius_services.communication.twilio_client import InMemoryTwilioClient


def test_local_environment_uses_in_memory_clients(monkeypatch):
    monkeypatch.setenv("APP_ENV", "local")
    reset_communication_providers()

    assert isinstance(get_message_sender(), InMemoryTwilioClient)
    assert isinstance(get_report_sender(), InMemoryEmailService)


def test_non_local_environment_uses_external_clients(monkeypatch, mocker):
    monkeypatch.setenv("APP_ENV", "dev")
    reset_communication_providers()
    twilio_cls = mocker.patch("julius_services.communication.providers.TwilioClient", autospec=True)
    email_cls = mocker.patch("julius_services.communication.providers.EmailService", autospec=True)

    get_message_sender()
    get_report_sender()

    twilio_cls.assert_called_once_with()
    email_cls.assert_called_once_with()
