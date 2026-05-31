from krabs_services.finance.investec_client import (
    InvestecAccountsClient,
    InvestecClient,
    InvestecDocumentsClient,
    InvestecPaymentsClient,
)
from krabs_tools.registry import Tool
from krabs_tools.tools.investec_accounts import (
    GetAccountsTool,
    GetBalanceTool,
    GetBulkBalancesTool,
    GetPendingTransactionsTool,
    GetTransactionsTool,
)
from krabs_tools.tools.investec_documents import GetDocumentsTool, GetDocumentTool
from krabs_tools.tools.investec_payments import (
    GetBeneficiariesTool,
    GetBeneficiaryCategoriesTool,
    PayBeneficiariesTool,
    TransferFundsTool,
)


def create_investec_account_tools(accounts_client: InvestecAccountsClient) -> list[Tool]:
    return [
        GetAccountsTool(accounts_client),
        GetBalanceTool(accounts_client),
        GetBulkBalancesTool(accounts_client),
        GetTransactionsTool(accounts_client),
        GetPendingTransactionsTool(accounts_client),
    ]


def create_investec_document_tools(documents_client: InvestecDocumentsClient) -> list[Tool]:
    return [
        GetDocumentsTool(documents_client),
        GetDocumentTool(documents_client),
    ]


def create_investec_payment_tools(payments_client: InvestecPaymentsClient) -> list[Tool]:
    return [
        TransferFundsTool(payments_client),
        GetBeneficiariesTool(payments_client),
        GetBeneficiaryCategoriesTool(payments_client),
        PayBeneficiariesTool(payments_client),
    ]


def create_investec_tools(investec_client: InvestecClient) -> list[Tool]:
    return [
        *create_investec_account_tools(investec_client.accounts),
        *create_investec_document_tools(investec_client.documents),
        *create_investec_payment_tools(investec_client.payments),
    ]
