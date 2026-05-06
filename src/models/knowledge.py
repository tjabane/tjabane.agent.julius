from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid

class MemoryType(str, Enum):
    PREFERENCE = "preference"
    HABIT = "habit"
    FACT = "fact"

class Memory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MemoryType
    content: str
    created_at: datetime = Field(default_factory=datetime.datetime.timezone.utc)
    last_referenced: datetime = Field(default_factory=datetime.datetime.timezone.utc)

class Skill(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    content: str
    created_at: datetime = Field(default_factory=datetime.datetime.timezone.utc)
    updated_at: datetime = Field(default_factory=datetime.datetime.timezone.utc)