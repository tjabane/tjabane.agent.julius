from __future__ import annotations

from krabs_domain.contracts import EmailService
from krabs_services.communication.email_service import AzureEmailService
from krabs_services.communication.protocols import MessageSender
from krabs_services.communication.twilio_client import TwilioClient

_message_sender: MessageSender | None = None
_report_sender: EmailService | None = None


def get_message_sender() -> MessageSender:
    global _message_sender
    if _message_sender is None:
        _message_sender = TwilioClient()
    return _message_sender


def get_report_sender() -> EmailService:
    global _report_sender
    if _report_sender is None:
        _report_sender = AzureEmailService()
    return _report_sender


def reset_communication_providers() -> None:
    global _message_sender, _report_sender
    _message_sender = None
    _report_sender = None
