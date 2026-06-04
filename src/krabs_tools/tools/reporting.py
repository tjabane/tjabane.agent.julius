from __future__ import annotations

from collections.abc import Callable

from krabs_domain.contracts import EmailService
from krabs_domain.models.reporting import Report
from krabs_domain.repositories.reporting import ReportRepository
from krabs_tools.schema.reporting import SendReportEmailInput


class SendReportEmailTool:
    name = "send_report_email"
    description = (
        "Email a manually generated spending report and store a copy for later review. "
        "Use this only when the user explicitly asks to email the report."
    )
    input_schema = SendReportEmailInput

    def __init__(
        self,
        email_service: EmailService,
        report_repository: ReportRepository | Callable[[], ReportRepository],
    ) -> None:
        self._email_service = email_service
        self._report_repository = report_repository if not callable(report_repository) else None
        self._report_repository_factory = report_repository if callable(report_repository) else None

    def _get_report_repository(self) -> ReportRepository:
        if self._report_repository is None:
            if self._report_repository_factory is None:
                msg = "Report repository factory is not configured."
                raise RuntimeError(msg)
            self._report_repository = self._report_repository_factory()
        return self._report_repository

    async def run(self, input_data: SendReportEmailInput) -> dict[str, str]:
        self._email_service.send_report(subject=input_data.subject, body=input_data.body)
        report = Report(
            query=input_data.query,
            content=input_data.body,
            schedule_id=input_data.schedule_id,
        )
        saved_report = self._get_report_repository().save(report)
        return {
            "status": "sent",
            "report_id": saved_report.id,
            "subject": input_data.subject,
            "created_at": saved_report.created_at.isoformat(),
        }
