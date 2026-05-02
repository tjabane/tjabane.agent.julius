from models.report import Report
from repositories.reports import ReportRepository
from services.email_service import EmailService

_repo = ReportRepository()
_email = EmailService()

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
    _repo.save(report)
    _email.send_report(subject=inputs["subject"], body=inputs["body"])
    return f"Report emailed and saved with ID {report.id}."
