from julius_services.communication.email_service import InMemoryEmailService
from julius_services.communication.providers import (
    get_message_sender,
    get_report_sender,
    reset_communication_providers,
)
from julius_services.communication.twilio_client import InMemoryTwilioClient


def test_local_environment_uses_in_memory_clients(monkeypatch):
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.delenv("COMMUNICATION_PROVIDER", raising=False)
    reset_communication_providers()

    assert isinstance(get_message_sender(), InMemoryTwilioClient)
    assert isinstance(get_report_sender(), InMemoryEmailService)


def test_external_provider_uses_external_clients(monkeypatch, mocker):
    monkeypatch.setenv("COMMUNICATION_PROVIDER", "external")
    reset_communication_providers()
    twilio_cls = mocker.patch("julius_services.communication.providers.TwilioClient", autospec=True)
    email_cls = mocker.patch("julius_services.communication.providers.EmailService", autospec=True)

    get_message_sender()
    get_report_sender()

    twilio_cls.assert_called_once_with()
    email_cls.assert_called_once_with()


def test_memory_provider_overrides_non_local_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("COMMUNICATION_PROVIDER", "memory")
    reset_communication_providers()

    assert isinstance(get_message_sender(), InMemoryTwilioClient)
    assert isinstance(get_report_sender(), InMemoryEmailService)
