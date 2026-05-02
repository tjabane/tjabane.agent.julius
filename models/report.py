from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class Report(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    content: str
    schedule_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
