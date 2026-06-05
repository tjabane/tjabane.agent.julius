from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DateRangeName = Literal[
    "today",
    "yesterday",
    "this_week",
    "last_week",
    "this_month",
    "last_month",
    "last_7_days",
    "last_30_days",
    "year_to_date",
]


class GetCurrentDateTimeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timezone: str = Field(
        default="Africa/Johannesburg",
        description="IANA timezone name.",
        examples=["Africa/Johannesburg", "UTC"],
    )


class ResolveDateRangeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    range: DateRangeName
    timezone: str = Field(
        default="Africa/Johannesburg",
        description="IANA timezone name.",
        examples=["Africa/Johannesburg", "UTC"],
    )
    reference_date: str | None = Field(
        default=None,
        description="Optional YYYY-MM-DD date to resolve relative ranges from. Defaults to today's date in the timezone.",
        examples=["2026-05-21"],
    )
