import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Frequency(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"


class Schedule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    frequency: Frequency
    next_run: datetime
    enabled: bool = True
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class Report(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    content: str
    schedule_id: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
