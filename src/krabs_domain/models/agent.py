from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Literal


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=_utcnow)


class Session(BaseModel):
    id: str
    whatsapp_number: str
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
