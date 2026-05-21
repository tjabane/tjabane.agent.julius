from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TIMEZONE = "Africa/Johannesburg"

DEFINITIONS = [
    {
        "name": "get_current_datetime",
        "description": "Get the current date and time for a timezone. Use this before interpreting relative dates like today, yesterday, this week, or next month.",
        "input_schema": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": f"IANA timezone name. Defaults to {DEFAULT_TIMEZONE}.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "resolve_date_range",
        "description": "Resolve a relative date range into concrete YYYY-MM-DD start and end dates for reports, schedules, statements, and transaction queries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "range": {
                    "type": "string",
                    "enum": [
                        "today",
                        "yesterday",
                        "this_week",
                        "last_week",
                        "this_month",
                        "last_month",
                        "last_7_days",
                        "last_30_days",
                        "year_to_date",
                    ],
                },
                "timezone": {
                    "type": "string",
                    "description": f"IANA timezone name. Defaults to {DEFAULT_TIMEZONE}.",
                },
                "reference_date": {
                    "type": "string",
                    "description": "Optional YYYY-MM-DD date to resolve relative ranges from. Defaults to today's date in the timezone.",
                },
            },
            "required": ["range"],
        },
    },
]


def handle(tool_name: str, inputs: dict, deps=None) -> str:
    if tool_name == "get_current_datetime":
        timezone_name = inputs.get("timezone", DEFAULT_TIMEZONE)
        now = datetime.now(_timezone(timezone_name))
        return str(
            {
                "timezone": timezone_name,
                "iso_datetime": now.isoformat(),
                "date": now.date().isoformat(),
                "time": now.strftime("%H:%M:%S"),
                "day_of_week": now.strftime("%A"),
                "utc_offset": now.strftime("%z"),
            }
        )

    if tool_name == "resolve_date_range":
        timezone_name = inputs.get("timezone", DEFAULT_TIMEZONE)
        today = _reference_date(inputs.get("reference_date"), timezone_name)
        start, end = _date_range(inputs["range"], today)
        return str(
            {
                "range": inputs["range"],
                "timezone": timezone_name,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "start_datetime": datetime.combine(start, time.min, tzinfo=_timezone(timezone_name)).isoformat(),
                "end_datetime": datetime.combine(end, time.max, tzinfo=_timezone(timezone_name)).isoformat(),
            }
        )

    raise ValueError(f"Unknown datetime tool: {tool_name}")


def _timezone(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown timezone: {timezone_name}") from exc


def _reference_date(value: str | None, timezone_name: str) -> date:
    if not value:
        return datetime.now(_timezone(timezone_name)).date()
    return date.fromisoformat(value)


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
