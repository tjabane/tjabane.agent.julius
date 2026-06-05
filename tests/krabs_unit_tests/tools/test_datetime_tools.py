import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from krabs_tools.schema import GetCurrentDateTimeInput, ResolveDateRangeInput
from krabs_tools.tools import GetCurrentDateTimeTool, ResolveDateRangeTool


def fixed_clock(timezone: ZoneInfo) -> datetime:
    return datetime(2026, 5, 21, 14, 30, 15, tzinfo=timezone)


class TestGetCurrentDateTimeTool:
    def test_returns_current_datetime_for_default_timezone(self):
        tool = GetCurrentDateTimeTool(clock=fixed_clock)

        result = asyncio.run(tool.run(GetCurrentDateTimeInput()))

        assert result == {
            "timezone": "Africa/Johannesburg",
            "iso_datetime": "2026-05-21T14:30:15+02:00",
            "date": "2026-05-21",
            "time": "14:30:15",
            "day_of_week": "Thursday",
            "utc_offset": "+0200",
        }

    def test_rejects_unknown_timezone(self):
        tool = GetCurrentDateTimeTool(clock=fixed_clock)

        with pytest.raises(ValueError, match="Unknown timezone"):
            asyncio.run(tool.run(GetCurrentDateTimeInput(timezone="Nowhere/Atlantis")))


class TestResolveDateRangeTool:
    @pytest.mark.parametrize(
        ("range_name", "start_date", "end_date"),
        [
            ("today", "2026-05-21", "2026-05-21"),
            ("yesterday", "2026-05-20", "2026-05-20"),
            ("this_week", "2026-05-18", "2026-05-21"),
            ("last_week", "2026-05-11", "2026-05-17"),
            ("this_month", "2026-05-01", "2026-05-21"),
            ("last_month", "2026-04-01", "2026-04-30"),
            ("last_7_days", "2026-05-15", "2026-05-21"),
            ("last_30_days", "2026-04-22", "2026-05-21"),
            ("year_to_date", "2026-01-01", "2026-05-21"),
        ],
    )
    def test_resolves_relative_range_from_reference_date(self, range_name, start_date, end_date):
        tool = ResolveDateRangeTool(clock=fixed_clock)

        result = asyncio.run(
            tool.run(
                ResolveDateRangeInput(
                    range=range_name,
                    reference_date="2026-05-21",
                )
            )
        )

        assert result["start_date"] == start_date
        assert result["end_date"] == end_date
        assert result["timezone"] == "Africa/Johannesburg"

    def test_resolves_relative_range_from_clock_when_reference_date_is_not_supplied(self):
        tool = ResolveDateRangeTool(clock=fixed_clock)

        result = asyncio.run(tool.run(ResolveDateRangeInput(range="today")))

        assert result["start_date"] == "2026-05-21"
        assert result["end_date"] == "2026-05-21"

    def test_accepts_timezone(self):
        tool = ResolveDateRangeTool(clock=fixed_clock)

        result = asyncio.run(
            tool.run(
                ResolveDateRangeInput(
                    range="today",
                    timezone="UTC",
                    reference_date="2026-05-21",
                )
            )
        )

        assert result["timezone"] == "UTC"
        assert result["start_datetime"].endswith("+00:00")
