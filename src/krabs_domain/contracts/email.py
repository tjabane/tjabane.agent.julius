from __future__ import annotations

from typing import Protocol


class EmailService(Protocol):
    def send_report(self, subject: str, body: str) -> None: ...
