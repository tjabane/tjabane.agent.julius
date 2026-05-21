from __future__ import annotations

import os
import re
from hashlib import sha256
from typing import Any

from langfuse import Langfuse

_client: Langfuse | None = None

_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.\w+\b")
_PHONE_RE = re.compile(r"(?<!\w)\+?\d[\d\s().-]{7,}\d(?!\w)")
_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


def get_langfuse_client() -> Langfuse:
    global _client
    if _client is None:
        _client = Langfuse(
            tracing_enabled=_tracing_enabled(),
            mask=mask_sensitive_data,
        )
    return _client


def stable_trace_identifier(value: str) -> str:
    salt = os.environ.get("LANGFUSE_USER_ID_SALT", "")
    return sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()[:32]


def mask_sensitive_data(data: Any, **_: Any) -> Any:
    if isinstance(data, str):
        return _mask_string(data)
    if isinstance(data, dict):
        return {key: mask_sensitive_data(value) for key, value in data.items()}
    if isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    if isinstance(data, tuple):
        return tuple(mask_sensitive_data(item) for item in data)
    return data


def _tracing_enabled() -> bool:
    configured = os.environ.get("LANGFUSE_TRACING_ENABLED")
    if configured is not None:
        return configured.lower() == "true"
    return bool(os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"))


def _mask_string(value: str) -> str:
    masked = _EMAIL_RE.sub("[REDACTED_EMAIL]", value)
    masked = _PHONE_RE.sub("[REDACTED_PHONE]", masked)
    return _CARD_RE.sub("[REDACTED_CARD]", masked)
