from pydantic import BaseModel, ConfigDict, Field


class GetAccountsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GetBalanceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(min_length=1)


class GetBulkBalancesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_ids: list[str] = Field(min_length=1)


class GetTransactionsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(min_length=1)
    from_date: str | None = Field(
        default=None,
        description="Start date for the transaction search in YYYY-MM-DD format.",
        examples=["2026-05-01"],
    )
    to_date: str | None = Field(
        default=None,
        description="End date for the transaction search in YYYY-MM-DD format.",
        examples=["2026-05-31"],
    )
    transaction_type: str | None = None
    include_pending: bool = False


class GetPendingTransactionsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(min_length=1)
