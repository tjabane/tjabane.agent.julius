from datetime import datetime
from models.reporting import Schedule, Report
from .base import BaseRepository


class ScheduleRepository(BaseRepository):
    def __init__(self):
        super().__init__("schedules")

    def get(self, schedule_id: str) -> Schedule | None:
        data = self._get(schedule_id, partition_key=schedule_id)
        return Schedule(**data) if data else None

    def save(self, schedule: Schedule) -> Schedule:
        schedule.updated_at = datetime.utcnow()
        self._upsert(schedule)
        return schedule

    def delete(self, schedule_id: str) -> None:
        self._delete(schedule_id, partition_key=schedule_id)

    def list_all(self) -> list[Schedule]:
        rows = self._query("SELECT * FROM c")
        return [Schedule(**r) for r in rows]

    def list_due(self) -> list[Schedule]:
        now = datetime.utcnow().isoformat()
        rows = self._query(
            "SELECT * FROM c WHERE c.enabled = true AND c.next_run <= @now",
            [{"name": "@now", "value": now}],
        )
        return [Schedule(**r) for r in rows]


class ReportRepository(BaseRepository):
    def __init__(self):
        super().__init__("reports")

    def save(self, report: Report) -> Report:
        self._upsert(report)
        return report

    def list_recent(self, limit: int = 10) -> list[Report]:
        rows = self._query(
            f"SELECT TOP {limit} * FROM c ORDER BY c.created_at DESC"
        )
        return [Report(**r) for r in rows]
