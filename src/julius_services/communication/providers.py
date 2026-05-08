from __future__ import annotations

import os

from julius_services.communication.email_service import EmailService, InMemoryEmailService
from julius_services.communication.protocols import MessageSender, ReportSender
from julius_services.communication.twilio_client import InMemoryTwilioClient, TwilioClient

_message_sender: MessageSender | None = None
_report_sender: ReportSender | None = None


def is_local_environment() -> bool:
    return os.environ.get("APP_ENV", "local").lower() == "local"


def get_message_sender() -> MessageSender:
    global _message_sender
    if _message_sender is None:
        _message_sender = InMemoryTwilioClient() if is_local_environment() else TwilioClient()
    return _message_sender


def get_report_sender() -> ReportSender:
    global _report_sender
    if _report_sender is None:
        _report_sender = InMemoryEmailService() if is_local_environment() else EmailService()
    return _report_sender


def reset_communication_providers() -> None:
    global _message_sender, _report_sender
    _message_sender = None
    _report_sender = None
