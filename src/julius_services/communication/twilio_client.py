from twilio.rest import Client
import os

from julius_application.observability import hash_identifier, mark_success, set_attributes, start_span


class TwilioClient:
    def __init__(self):
        self._client = Client(
            os.environ["TWILIO_ACCOUNT_SID"],
            os.environ["TWILIO_AUTH_TOKEN"],
        )
        self._from_number = os.environ["TWILIO_WHATSAPP_NUMBER"]

    def send_message(self, to: str, body: str) -> None:
        with start_span("twilio.send_message", {
            "messaging.system": "twilio",
            "messaging.destination.hash": hash_identifier(to),
        }) as span:
            message = self._client.messages.create(
                from_=f"whatsapp:{self._from_number}",
                to=f"whatsapp:{to}",
                body=body,
            )
            set_attributes(span, {
                "twilio.message.sid_present": bool(getattr(message, "sid", None)),
            })
            mark_success(span)

    @staticmethod
    def parse_webhook(form_data: dict) -> tuple[str, str]:
        """Returns (sender_number, message_body) from a Twilio webhook payload."""
        number = form_data.get("From", "").replace("whatsapp:", "")
        body = form_data.get("Body", "")
        return number, body
