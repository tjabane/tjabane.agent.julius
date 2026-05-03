from models.report import Report
from repositories.reports import ReportRepository
from services.email_service import EmailService

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


def handle(tool_name: str, inputs: dict) -> str:
    report = Report(
        query=inputs["subject"],
        content=inputs["body"],
        schedule_id=inputs.get("schedule_id"),
    )
    _get_repo().save(report)
    _get_email().send_report(subject=inputs["subject"], body=inputs["body"])
    return f"Report emailed and saved with ID {report.id}."
