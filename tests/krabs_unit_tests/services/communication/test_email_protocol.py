from unittest.mock import patch

from krabs_domain.contracts import EmailService
from krabs_services.communication.email_service import AzureEmailService


def accepts_email_service(service: EmailService) -> EmailService:
    return service


@patch("krabs_services.communication.email_service.EmailClient")
def test_azure_email_service_satisfies_email_service_protocol(_mock_client, monkeypatch) -> None:
    monkeypatch.setenv("AZURE_COMMUNICATION_CONNECTION_STRING", "endpoint=https://test.communication.azure.com/;accesskey=dGVzdA==")
    monkeypatch.setenv("EMAIL_SENDER_ADDRESS", "DoNotReply@test.azurecomm.net")
    monkeypatch.setenv("EMAIL_RECIPIENT_ADDRESS", "user@example.com")
    service = AzureEmailService()

    assert accepts_email_service(service) is service
