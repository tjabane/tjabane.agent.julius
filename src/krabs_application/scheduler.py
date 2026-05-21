from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from krabs_agent.agent_runner import run_scheduled
from krabs_domain.models.reporting import Frequency
from krabs_domain.repositories.reporting import ScheduleRepository

_LOGGER = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self, schedules: ScheduleRepository | None = None) -> None:
        self._schedules = schedules or ScheduleRepository()

    def run_due(self) -> None:
        due = self._schedules.list_due()
        for schedule in due:
            try:
                run_scheduled(schedule_id=schedule.id, query=schedule.query)
                schedule.next_run = next_run(schedule.frequency)
                self._schedules.save(schedule)
            except Exception:
                _LOGGER.exception("Scheduled run failed for %s", schedule.id)


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
