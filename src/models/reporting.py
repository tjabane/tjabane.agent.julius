from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class Frequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"


class Schedule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    frequency: Frequency
    next_run: datetime
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Report(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    content: str
    schedule_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
