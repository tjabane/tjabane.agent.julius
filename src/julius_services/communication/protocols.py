from __future__ import annotations

from typing import Protocol


class MessageSender(Protocol):
    def send_message(self, to: str, body: str) -> None:
        ...


class ReportSender(Protocol):
    def send_report(self, subject: str, body: str) -> None:
        ...
