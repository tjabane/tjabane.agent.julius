import ast

import pytest

from krabs_agent.tools import ALL_DEFINITIONS, dispatch


def _result_dict(result: str) -> dict:
    return ast.literal_eval(result)


class TestDatetimeTools:
    def test_definitions_are_registered(self):
        names = {tool["function"]["name"] for tool in ALL_DEFINITIONS}

        assert "get_current_datetime" in names
        assert "resolve_date_range" in names

    def test_get_current_datetime_defaults_to_south_africa_timezone(self):
        result = _result_dict(dispatch("get_current_datetime", {}))

        assert result["timezone"] == "Africa/Johannesburg"
        assert result["date"]
        assert result["time"]
        assert result["day_of_week"]

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
    def test_resolve_date_range(self, range_name, start_date, end_date):
        result = _result_dict(
            dispatch(
                "resolve_date_range",
                {
                    "range": range_name,
                    "reference_date": "2026-05-21",
                },
            )
        )

        assert result["start_date"] == start_date
        assert result["end_date"] == end_date
        assert result["timezone"] == "Africa/Johannesburg"

    def test_resolve_date_range_accepts_timezone(self):
        result = _result_dict(
            dispatch(
                "resolve_date_range",
                {
                    "range": "today",
                    "timezone": "UTC",
                    "reference_date": "2026-05-21",
                },
            )
        )

        assert result["timezone"] == "UTC"
        assert result["start_datetime"].endswith("+00:00")

    def test_rejects_unknown_timezone(self):
        with pytest.raises(ValueError, match="Unknown timezone"):
            dispatch("get_current_datetime", {"timezone": "Nowhere/Atlantis"})
