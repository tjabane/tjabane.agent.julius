from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from hashlib import sha256
from hmac import new as hmac_new
from uuid import uuid4


@dataclass(frozen=True)
class TurnContext:
    turn_id: str
    session_id: str


_current_turn_context: ContextVar[TurnContext | None] = ContextVar("krabs_turn_context", default=None)


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


def create_turn_context_from_env(whatsapp_number: str, *, turn_id: str | None = None) -> TurnContext:
    secret = os.environ.get("OTEL_SESSION_ID_SECRET", "local-observability-session-secret")
    return create_turn_context(whatsapp_number, secret=secret, turn_id=turn_id)


def current_turn_context() -> TurnContext | None:
    return _current_turn_context.get()


@contextmanager
def use_turn_context(turn_context: TurnContext) -> Iterator[TurnContext]:
    token = _current_turn_context.set(turn_context)
    try:
        yield turn_context
    finally:
        _current_turn_context.reset(token)


def _normalize_whatsapp_number(whatsapp_number: str) -> str:
    return whatsapp_number.strip().removeprefix("whatsapp:").strip()
