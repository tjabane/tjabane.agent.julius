from azure.communication.email import EmailClient
import os

from julius_application.observability import hash_identifier, mark_success, start_span


class EmailService:
    def __init__(self):
        self._client = EmailClient.from_connection_string(
            os.environ["AZURE_COMMUNICATION_CONNECTION_STRING"]
        )
        self._sender = os.environ["EMAIL_SENDER_ADDRESS"]
        self._recipient = os.environ["EMAIL_RECIPIENT_ADDRESS"]

    def send_report(self, subject: str, body: str) -> None:
        with start_span("email.send_report", {
            "messaging.system": "azure_communication_email",
            "messaging.destination.hash": hash_identifier(self._recipient),
        }) as span:
            message = {
                "senderAddress": self._sender,
                "recipients": {"to": [{"address": self._recipient}]},
                "content": {"subject": subject, "plainText": body},
            }
            poller = self._client.begin_send(message)
            poller.result()
            mark_success(span)
