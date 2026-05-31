from pydantic import BaseModel, ConfigDict, Field


class GetAccountsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GetBalanceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(min_length=1)


class GetTransactionsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(min_length=1)
    from_date: str | None = None
    to_date: str | None = None
    transaction_type: str | None = None
    include_pending: bool = False


class GetPendingTransactionsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(min_length=1)
