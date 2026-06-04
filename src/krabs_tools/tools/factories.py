from krabs_domain.contracts import BankingClient
from krabs_tools.registry import Tool
from krabs_tools.tools.banking_accounts import (
    GetAccountsTool,
    GetBalanceTool,
    GetBulkBalancesTool,
    GetPendingTransactionsTool,
    GetTransactionsTool,
)
from krabs_tools.tools.banking_documents import GetDocumentsTool, GetDocumentTool
from krabs_tools.tools.banking_payments import (
    GetBeneficiariesTool,
    GetBeneficiaryCategoriesTool,
    PayBeneficiariesTool,
    TransferFundsTool,
)


def create_banking_account_tools(banking_client: BankingClient) -> list[Tool]:
    return [
        GetAccountsTool(banking_client),
        GetBalanceTool(banking_client),
        GetBulkBalancesTool(banking_client),
        GetTransactionsTool(banking_client),
        GetPendingTransactionsTool(banking_client),
    ]


def create_banking_document_tools(banking_client: BankingClient) -> list[Tool]:
    return [
        GetDocumentsTool(banking_client),
        GetDocumentTool(banking_client),
    ]


def create_banking_payment_tools(banking_client: BankingClient) -> list[Tool]:
    return [
        TransferFundsTool(banking_client),
        GetBeneficiariesTool(banking_client),
        GetBeneficiaryCategoriesTool(banking_client),
        PayBeneficiariesTool(banking_client),
    ]


def create_banking_tools(banking_client: BankingClient) -> list[Tool]:
    return [
        *create_banking_account_tools(banking_client),
        *create_banking_document_tools(banking_client),
        *create_banking_payment_tools(banking_client),
    ]
