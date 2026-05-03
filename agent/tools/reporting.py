from __future__ import annotations
from typing import TYPE_CHECKING
from models.reporting import Report
from repositories.reporting import ReportRepository
from services.email_service import EmailService

if TYPE_CHECKING:
    from agent.tools.deps import ToolDeps

_repo: ReportRepository | None = None
_email: EmailService | None = None


def _get_repo() -> ReportRepository:
    global _repo
    if _repo is None:
        _repo = ReportRepository()
    return _repo


def _get_email() -> EmailService:
    global _email
    if _email is None:
        _email = EmailService()
    return _email


DEFINITIONS = [
    {
        "name": "send_email",
        "description": "Send a financial report to the user's email address.",
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "body": {"type": "string", "description": "The full report content in plain text"},
                "schedule_id": {"type": "string", "description": "Optional: ID of the schedule that triggered this report"},
            },
            "required": ["subject", "body"],
        },
    }
]


def handle(tool_name: str, inputs: dict, deps: ToolDeps | None = None) -> str:
    repo = (deps.report_repo if deps and deps.report_repo else None) or _get_repo()
    email = (deps.email if deps and deps.email else None) or _get_email()

    report = Report(
        query=inputs["subject"],
        content=inputs["body"],
        schedule_id=inputs.get("schedule_id"),
    )
    repo.save(report)
    email.send_report(subject=inputs["subject"], body=inputs["body"])
    return f"Report emailed and saved with ID {report.id}."
