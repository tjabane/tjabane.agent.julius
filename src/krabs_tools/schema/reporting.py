from pydantic import BaseModel, ConfigDict, Field


class SendReportEmailInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(
        min_length=1,
        description="The user's report request or summary title to store with the emailed report.",
    )
    subject: str = Field(
        min_length=1,
        description="The email subject line for the report.",
    )
    body: str = Field(
        min_length=1,
        description="The full report body to email and store.",
    )
    schedule_id: str | None = Field(
        default=None,
        description="Optional schedule identifier if the report is associated with a recurring schedule.",
    )
