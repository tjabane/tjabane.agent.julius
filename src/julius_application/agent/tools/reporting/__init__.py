from __future__ import annotations
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from julius_domain.models.reporting import Schedule, Frequency, Report
from julius_domain.repositories.reporting import ScheduleRepository, ReportRepository
from julius_services.communication.email_service import EmailService

if TYPE_CHECKING:
    from julius_application.agent.tools.deps import ToolDeps

_schedule_repo: ScheduleRepository | None = None
_report_repo: ReportRepository | None = None
_email: EmailService | None = None


def _get_schedule_repo() -> ScheduleRepository:
    global _schedule_repo
    if _schedule_repo is None:
        _schedule_repo = ScheduleRepository()
    return _schedule_repo


def _get_report_repo() -> ReportRepository:
    global _report_repo
    if _report_repo is None:
        _report_repo = ReportRepository()
    return _report_repo


def _get_email() -> EmailService:
    global _email
    if _email is None:
        _email = EmailService()
    return _email


def _next_run_default(frequency: Frequency) -> datetime:
    tomorrow = datetime.utcnow().replace(hour=6, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return tomorrow


DEFINITIONS = [
    {
        "name": "manage_schedule",
        "description": "Create, update, enable, disable, or delete a scheduled report.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "update", "delete", "list", "enable", "disable"],
                },
                "schedule_id": {"type": "string", "description": "Required for update, delete, enable, disable"},
                "query": {"type": "string", "description": "The report query to run on schedule"},
                "frequency": {"type": "string", "enum": ["daily", "weekly"]},
                "next_run": {"type": "string", "description": "ISO datetime for next run. Defaults to tomorrow 08:00 if not provided."},
            },
            "required": ["action"],
        },
    },
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
    },
]


def handle(tool_name: str, inputs: dict, deps: ToolDeps | None = None) -> str:
    if tool_name == "manage_schedule":
        repo = (deps.schedule_repo if deps and deps.schedule_repo else None) or _get_schedule_repo()
        action = inputs["action"]

        if action == "list":
            schedules = repo.list_all()
            if not schedules:
                return "No schedules configured."
            return "\n".join(
                f"[{s.id}] {s.frequency.value} — '{s.query}' — next run: {s.next_run.isoformat()} — {'enabled' if s.enabled else 'disabled'}"
                for s in schedules
            )

        if action == "create":
            frequency = Frequency(inputs["frequency"])
            next_run = datetime.fromisoformat(inputs["next_run"]) if inputs.get("next_run") else _next_run_default(frequency)
            schedule = Schedule(query=inputs["query"], frequency=frequency, next_run=next_run)
            repo.save(schedule)
            return f"Schedule created with ID {schedule.id}. Runs {frequency.value}, next at {next_run.isoformat()}."

        if action == "update":
            schedule = repo.get(inputs["schedule_id"])
            if not schedule:
                return f"Schedule {inputs['schedule_id']} not found."
            if "query" in inputs:
                schedule.query = inputs["query"]
            if "frequency" in inputs:
                schedule.frequency = Frequency(inputs["frequency"])
            if "next_run" in inputs:
                schedule.next_run = datetime.fromisoformat(inputs["next_run"])
            repo.save(schedule)
            return f"Schedule {schedule.id} updated."

        if action in ("enable", "disable"):
            schedule = repo.get(inputs["schedule_id"])
            if not schedule:
                return f"Schedule {inputs['schedule_id']} not found."
            schedule.enabled = action == "enable"
            repo.save(schedule)
            return f"Schedule {schedule.id} {action}d."

        if action == "delete":
            repo.delete(inputs["schedule_id"])
            return f"Schedule {inputs['schedule_id']} deleted."

        raise ValueError(f"Unknown schedule action: {action}")

    if tool_name == "send_email":
        repo = (deps.report_repo if deps and deps.report_repo else None) or _get_report_repo()
        email = (deps.email if deps and deps.email else None) or _get_email()
        report = Report(
            query=inputs["subject"],
            content=inputs["body"],
            schedule_id=inputs.get("schedule_id"),
        )
        repo.save(report)
        email.send_report(subject=inputs["subject"], body=inputs["body"])
        return f"Report emailed and saved with ID {report.id}."

    raise ValueError(f"Unknown reporting tool: {tool_name}")
