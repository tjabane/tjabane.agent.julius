from krabs_tools.tools import (
    GetAccountsTool,
    GetBalanceTool,
    GetBeneficiariesTool,
    GetBeneficiaryCategoriesTool,
    GetBulkBalancesTool,
    GetDocumentsTool,
    GetDocumentTool,
    GetPendingTransactionsTool,
    GetTransactionsTool,
    PayBeneficiariesTool,
    TransferFundsTool,
    create_investec_account_tools,
    create_investec_document_tools,
    create_investec_payment_tools,
    create_investec_tools,
)


class FakeInvestecClient:
    def __init__(self) -> None:
        self.accounts = object()
        self.documents = object()
        self.payments = object()


def test_create_investec_account_tools_returns_account_tools_with_shared_client():
    accounts_client = object()

    tools = create_investec_account_tools(accounts_client)

    assert [type(tool) for tool in tools] == [
        GetAccountsTool,
        GetBalanceTool,
        GetBulkBalancesTool,
        GetTransactionsTool,
        GetPendingTransactionsTool,
    ]
    assert all(tool._accounts_client is accounts_client for tool in tools)


def test_create_investec_document_tools_returns_document_tools_with_shared_client():
    documents_client = object()

    tools = create_investec_document_tools(documents_client)

    assert [type(tool) for tool in tools] == [
        GetDocumentsTool,
        GetDocumentTool,
    ]
    assert all(tool._documents_client is documents_client for tool in tools)


def test_create_investec_payment_tools_returns_payment_tools_with_shared_client():
    payments_client = object()

    tools = create_investec_payment_tools(payments_client)

    assert [type(tool) for tool in tools] == [
        TransferFundsTool,
        GetBeneficiariesTool,
        GetBeneficiaryCategoriesTool,
        PayBeneficiariesTool,
    ]
    assert all(tool._payments_client is payments_client for tool in tools)


def test_create_investec_tools_combines_all_grouped_factories():
    investec_client = FakeInvestecClient()

    tools = create_investec_tools(investec_client)

    assert [tool.name for tool in tools] == [
        "get_accounts",
        "get_balance",
        "get_bulk_balances",
        "get_transactions",
        "get_pending_transactions",
        "get_documents",
        "get_document",
        "transfer_funds",
        "get_beneficiaries",
        "get_beneficiary_categories",
        "pay_beneficiaries",
    ]
