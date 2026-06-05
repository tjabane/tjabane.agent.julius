from pydantic import BaseModel, ConfigDict, Field


class GetDocumentsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(min_length=1)
    from_date: str = Field(
        description="Start date for the document search in YYYY-MM-DD format.",
        examples=["2026-05-01"],
    )
    to_date: str = Field(
        description="End date for the document search in YYYY-MM-DD format.",
        examples=["2026-05-31"],
    )


class GetDocumentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(min_length=1)
    document_type: str = Field(
        min_length=1,
        description="Investec document type path value, for example STATEMENT.",
    )
    document_date: str = Field(
        description="Document date in YYYY-MM-DD format.",
        examples=["2026-05-31"],
    )
