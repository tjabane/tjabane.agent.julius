from typing import Any

from krabs_domain.contracts import BankingClient
from krabs_tools.schema.banking_documents import GetDocumentInput, GetDocumentsInput


class GetDocumentsTool:
    name = "get_documents"
    description = "Get bank documents for an account within a date range."
    input_schema = GetDocumentsInput

    def __init__(self, banking_client: BankingClient) -> None:
        self._banking_client = banking_client

    async def run(self, input_data: GetDocumentsInput) -> list[dict[str, Any]]:
        return self._banking_client.get_documents(
            account_id=input_data.account_id,
            from_date=input_data.from_date,
            to_date=input_data.to_date,
        )


class GetDocumentTool:
    name = "get_document"
    description = "Get a specific bank document for an account by document type and document date."
    input_schema = GetDocumentInput

    def __init__(self, banking_client: BankingClient) -> None:
        self._banking_client = banking_client

    async def run(self, input_data: GetDocumentInput) -> Any:
        return self._banking_client.get_document(
            account_id=input_data.account_id,
            document_type=input_data.document_type,
            document_date=input_data.document_date,
        )
