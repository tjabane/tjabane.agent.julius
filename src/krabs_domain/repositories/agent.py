from datetime import UTC, datetime

from krabs_domain.models.agent import Session
from krabs_observability.semantic import AttributeName, SpanName
from krabs_observability.telemetry import trace_operation

from .base import BaseRepository

_SESSION_ATTRS = {AttributeName.OPERATION_NAME}


def _utcnow() -> datetime:
    return datetime.now(UTC)


class SessionRepository(BaseRepository):
    def __init__(self):
        super().__init__("sessions")

    def get(self, whatsapp_number: str) -> Session | None:
        with trace_operation(
            SpanName.SESSION_LOAD,
            attributes={AttributeName.OPERATION_NAME: "session.get"},
            allowed_attribute_names=_SESSION_ATTRS,
        ):
            data = self._get(whatsapp_number, partition_key=whatsapp_number)
        return Session(**data) if data else None

    def save(self, session: Session) -> Session:
        with trace_operation(
            SpanName.SESSION_SAVE,
            attributes={AttributeName.OPERATION_NAME: "session.save"},
            allowed_attribute_names=_SESSION_ATTRS,
        ):
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
