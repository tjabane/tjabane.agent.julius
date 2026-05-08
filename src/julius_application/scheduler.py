from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from julius_application.agent.agent import run_scheduled
from julius_application.observability import mark_success, record_exception, start_span
from julius_domain.models.reporting import Frequency
from julius_domain.repositories.reporting import ScheduleRepository

_LOGGER = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self, schedules: ScheduleRepository | None = None) -> None:
        self._schedules = schedules or ScheduleRepository()

    def run_due(self) -> None:
        with start_span("scheduler.run", {"app.operation": "scheduler"}) as span:
            due = self._schedules.list_due()
            span.set_attribute("scheduler.due_count", len(due))
            for schedule in due:
                with start_span("scheduled_report.run", {"app.schedule_id": schedule.id}) as child_span:
                    try:
                        run_scheduled(schedule_id=schedule.id, query=schedule.query)
                        schedule.next_run = next_run(schedule.frequency)
                        self._schedules.save(schedule)
                        mark_success(child_span)
                    except Exception as exc:
                        record_exception(child_span, exc)
                        _LOGGER.exception("Scheduled run failed for %s", schedule.id)
            mark_success(span)


def next_run(frequency: Frequency) -> datetime:
    base = datetime.now(timezone.utc).replace(hour=6, minute=0, second=0, microsecond=0)
    if frequency == Frequency.DAILY:
        return base + timedelta(days=1)
    return base + timedelta(weeks=1)


async def run_scheduler_loop(
    service: SchedulerService | None = None,
    interval_seconds: int = 300,
    stop_event: asyncio.Event | None = None,
) -> None:
    scheduler = service or SchedulerService()
    stop = stop_event or asyncio.Event()
    while not stop.is_set():
        try:
            await asyncio.to_thread(scheduler.run_due)
        except Exception:
            _LOGGER.exception("Scheduler loop failed")

        try:
            await asyncio.wait_for(stop.wait(), timeout=interval_seconds)
        except TimeoutError:
            continue
