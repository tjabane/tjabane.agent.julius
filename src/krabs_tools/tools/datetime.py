from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from krabs_tools.schema.datetime import GetCurrentDateTimeInput, ResolveDateRangeInput

DEFAULT_TIMEZONE = "Africa/Johannesburg"


def _default_clock(timezone: ZoneInfo) -> datetime:
    return datetime.now(timezone)


class GetCurrentDateTimeTool:
    name = "get_current_datetime"
    description = (
        "Get the current date and time for a timezone. Use this before interpreting relative dates "
        "like today, yesterday, this week, or next month."
    )
    input_schema = GetCurrentDateTimeInput

    def __init__(self, clock: Callable[[ZoneInfo], datetime] = _default_clock) -> None:
        self._clock = clock

    async def run(self, input_data: GetCurrentDateTimeInput) -> dict[str, str]:
        timezone = _timezone(input_data.timezone)
        now = self._clock(timezone)
        return {
            "timezone": input_data.timezone,
            "iso_datetime": now.isoformat(),
            "date": now.date().isoformat(),
            "time": now.strftime("%H:%M:%S"),
            "day_of_week": now.strftime("%A"),
            "utc_offset": now.strftime("%z"),
        }


class ResolveDateRangeTool:
    name = "resolve_date_range"
    description = (
        "Resolve a relative date range into concrete YYYY-MM-DD start and end dates for reports, "
        "statements, and transaction queries."
    )
    input_schema = ResolveDateRangeInput

    def __init__(self, clock: Callable[[ZoneInfo], datetime] = _default_clock) -> None:
        self._clock = clock

    async def run(self, input_data: ResolveDateRangeInput) -> dict[str, str]:
        timezone = _timezone(input_data.timezone)
        today = _reference_date(input_data.reference_date, timezone, self._clock)
        start, end = _date_range(input_data.range, today)
        return {
            "range": input_data.range,
            "timezone": input_data.timezone,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "start_datetime": datetime.combine(start, time.min, tzinfo=timezone).isoformat(),
            "end_datetime": datetime.combine(end, time.max, tzinfo=timezone).isoformat(),
        }


def _timezone(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown timezone: {timezone_name}") from exc


def _reference_date(
    value: str | None,
    timezone: ZoneInfo,
    clock: Callable[[ZoneInfo], datetime],
) -> date:
    if value:
        return date.fromisoformat(value)
    return clock(timezone).date()


def _date_range(range_name: str, today: date) -> tuple[date, date]:
    if range_name == "today":
        return today, today
    if range_name == "yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
    if range_name == "this_week":
        start = today - timedelta(days=today.weekday())
        return start, today
    if range_name == "last_week":
        this_week_start = today - timedelta(days=today.weekday())
        start = this_week_start - timedelta(days=7)
        return start, start + timedelta(days=6)
    if range_name == "this_month":
        return today.replace(day=1), today
    if range_name == "last_month":
        this_month_start = today.replace(day=1)
        end = this_month_start - timedelta(days=1)
        return end.replace(day=1), end
    if range_name == "last_7_days":
        return today - timedelta(days=6), today
    if range_name == "last_30_days":
        return today - timedelta(days=29), today
    if range_name == "year_to_date":
        return today.replace(month=1, day=1), today
    raise ValueError(f"Unknown date range: {range_name}")
