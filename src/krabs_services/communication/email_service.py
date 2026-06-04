import os
from dataclasses import dataclass

from azure.communication.email import EmailClient


@dataclass(frozen=True)
class SentReport:
    subject: str
    body: str


class AzureEmailService:
    def __init__(self):
        self._client = EmailClient.from_connection_string(
            os.environ["AZURE_COMMUNICATION_CONNECTION_STRING"]
        )
        self._sender = os.environ["EMAIL_SENDER_ADDRESS"]
        self._recipient = os.environ["EMAIL_RECIPIENT_ADDRESS"]

    def send_report(self, subject: str, body: str) -> None:
        message = {
            "senderAddress": self._sender,
            "recipients": {"to": [{"address": self._recipient}]},
            "content": {"subject": subject, "plainText": body},
        }
        poller = self._client.begin_send(message)
        poller.result()


class InMemoryEmailService:
    def __init__(self) -> None:
        self.sent_reports: list[SentReport] = []

    def send_report(self, subject: str, body: str) -> None:
        self.sent_reports.append(SentReport(subject=subject, body=body))
