from __future__ import annotations

import os
from typing import Literal

from julius_services.communication.email_service import EmailService, InMemoryEmailService
from julius_services.communication.protocols import MessageSender, ReportSender
from julius_services.communication.twilio_client import InMemoryTwilioClient, TwilioClient

CommunicationProvider = Literal["memory", "external"]

_message_sender: MessageSender | None = None
_report_sender: ReportSender | None = None


def get_communication_provider() -> CommunicationProvider:
    configured = os.environ.get("COMMUNICATION_PROVIDER")
    if configured:
        provider = configured.lower()
        if provider not in ("memory", "external"):
            raise ValueError("COMMUNICATION_PROVIDER must be 'memory' or 'external'")
        return provider

    app_environment = os.environ.get("APP_ENV", "local").lower()
    return "memory" if app_environment == "local" else "external"


def use_in_memory_communication() -> bool:
    return get_communication_provider() == "memory"


def get_message_sender() -> MessageSender:
    global _message_sender
    if _message_sender is None:
        _message_sender = InMemoryTwilioClient() if use_in_memory_communication() else TwilioClient()
    return _message_sender


def get_report_sender() -> ReportSender:
    global _report_sender
    if _report_sender is None:
        _report_sender = InMemoryEmailService() if use_in_memory_communication() else EmailService()
    return _report_sender


def reset_communication_providers() -> None:
    global _message_sender, _report_sender
    _message_sender = None
    _report_sender = None
