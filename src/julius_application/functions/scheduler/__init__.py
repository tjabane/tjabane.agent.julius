from datetime import datetime, timedelta, timezone
import logging
import azure.functions as func
from julius_domain.repositories.schedules import ScheduleRepository
from julius_domain.models.schedule import Frequency
from julius_application.agent.agent import run_scheduled

_repo = ScheduleRepository()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def main(timer: func.TimerRequest) -> None:
    due = _repo.list_due()
    if not due:
        return

    for schedule in due:
        try:
            run_scheduled(schedule_id=schedule.id, query=schedule.query)
            schedule.next_run = _next_run(schedule.frequency)
            _repo.save(schedule)
        except Exception as e:
            logging.error("Scheduled run failed for %s: %s", schedule.id, e)


def _next_run(frequency: Frequency) -> datetime:
    base = _utcnow().replace(hour=6, minute=0, second=0, microsecond=0)
    if frequency == Frequency.DAILY:
        return base + timedelta(days=1)
    return base + timedelta(weeks=1)
