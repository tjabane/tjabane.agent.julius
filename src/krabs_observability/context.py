from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from hmac import new as hmac_new
from uuid import uuid4


@dataclass(frozen=True)
class TurnContext:
    turn_id: str
    session_id: str


def create_turn_context(whatsapp_number: str, *, secret: str, turn_id: str | None = None) -> TurnContext:
    normalized_number = _normalize_whatsapp_number(whatsapp_number)
    digest = hmac_new(
        secret.encode("utf-8"),
        normalized_number.encode("utf-8"),
        sha256,
    ).hexdigest()
    return TurnContext(
        turn_id=turn_id or str(uuid4()),
        session_id=f"wa_{digest[:32]}",
    )


def _normalize_whatsapp_number(whatsapp_number: str) -> str:
    return whatsapp_number.strip().removeprefix("whatsapp:").strip()
