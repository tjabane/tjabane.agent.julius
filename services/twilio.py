from twilio.rest import Client
import os


class TwilioClient:
    def __init__(self):
        self._client = Client(
            os.environ["TWILIO_ACCOUNT_SID"],
            os.environ["TWILIO_AUTH_TOKEN"],
        )
        self._from_number = os.environ["TWILIO_WHATSAPP_NUMBER"]

    def send_message(self, to: str, body: str) -> None:
        self._client.messages.create(
            from_=f"whatsapp:{self._from_number}",
            to=f"whatsapp:{to}",
            body=body,
        )

    @staticmethod
    def parse_webhook(form_data: dict) -> tuple[str, str]:
        """Returns (sender_number, message_body) from a Twilio webhook payload."""
        number = form_data.get("From", "").replace("whatsapp:", "")
        body = form_data.get("Body", "")
        return number, body
