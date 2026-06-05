import asyncio
from datetime import UTC, datetime

from krabs_domain.models.reporting import Report
from krabs_domain.repositories.reporting import ReportRepository
from krabs_tools.schema import SendReportEmailInput
from krabs_tools.tools import SendReportEmailTool


class FakeEmailService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def send_report(self, subject: str, body: str) -> None:
        self.calls.append((subject, body))


class FakeReportRepository(ReportRepository):
    def __init__(self) -> None:
        self.calls: list[Report] = []

    def save(self, report: Report) -> Report:
        self.calls.append(report)
        report.id = "report-123"
        report.created_at = datetime(2026, 5, 21, 15, 45, 0, tzinfo=UTC)
        return report


def test_send_report_email_sends_and_persists_report():
    email_service = FakeEmailService()
    report_repository = FakeReportRepository()
    tool = SendReportEmailTool(email_service, report_repository)
    input_data = SendReportEmailInput(
        query="weekly spending scoreboard",
        subject="Weekly Spending Scoreboard",
        body="SPENDING SCOREBOARD\nSpent: R3860",
        schedule_id="schedule-123",
    )

    result = asyncio.run(tool.run(input_data))

    assert email_service.calls == [
        ("Weekly Spending Scoreboard", "SPENDING SCOREBOARD\nSpent: R3860"),
    ]
    assert len(report_repository.calls) == 1
    saved_report = report_repository.calls[0]
    assert saved_report.query == "weekly spending scoreboard"
    assert saved_report.content == "SPENDING SCOREBOARD\nSpent: R3860"
    assert saved_report.schedule_id == "schedule-123"
    assert result == {
        "status": "sent",
        "report_id": "report-123",
        "subject": "Weekly Spending Scoreboard",
        "created_at": "2026-05-21T15:45:00+00:00",
    }
