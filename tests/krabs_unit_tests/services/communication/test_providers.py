from krabs_services.communication.providers import (
    get_message_sender,
    get_report_sender,
    reset_communication_providers,
)


def test_get_message_sender_uses_twilio_client(mocker):
    reset_communication_providers()
    twilio_cls = mocker.patch("krabs_services.communication.providers.TwilioClient", autospec=True)

    get_message_sender()

    twilio_cls.assert_called_once_with()


def test_get_report_sender_uses_azure_email_service(mocker):
    reset_communication_providers()
    email_cls = mocker.patch("krabs_services.communication.providers.AzureEmailService", autospec=True)

    get_report_sender()

    email_cls.assert_called_once_with()


def test_provider_instances_are_cached(mocker):
    reset_communication_providers()
    twilio_cls = mocker.patch("krabs_services.communication.providers.TwilioClient", autospec=True)
    email_cls = mocker.patch("krabs_services.communication.providers.AzureEmailService", autospec=True)

    assert get_message_sender() is get_message_sender()
    assert get_report_sender() is get_report_sender()

    twilio_cls.assert_called_once_with()
    email_cls.assert_called_once_with()
