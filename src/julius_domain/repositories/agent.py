from datetime import datetime, timezone
from julius_domain.models.agent import Session
from .base import BaseRepository


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SessionRepository(BaseRepository):
    def __init__(self):
        super().__init__("sessions")

    def get(self, whatsapp_number: str) -> Session | None:
        data = self._get(whatsapp_number, partition_key=whatsapp_number)
        return Session(**data) if data else None

    def save(self, session: Session) -> Session:
        session.updated_at = _utcnow()
        session.id = session.whatsapp_number
        self._upsert(session)
        return session

    def get_or_create(self, whatsapp_number: str) -> Session:
        session = self.get(whatsapp_number)
        if not session:
            session = Session(id=whatsapp_number, whatsapp_number=whatsapp_number)
            self.save(session)
        return session
