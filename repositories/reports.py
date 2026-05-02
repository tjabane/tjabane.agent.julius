from models.report import Report
from .base import BaseRepository


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
