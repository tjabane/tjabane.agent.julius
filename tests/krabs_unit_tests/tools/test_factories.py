from typing import Any

from krabs_domain.contracts import BankingClient, EmailService
from krabs_domain.repositories.reporting import ReportRepository
from krabs_tools.tools import (
    GetAccountsTool,
    GetBalanceTool,
    GetBeneficiariesTool,
    GetBeneficiaryCategoriesTool,
    GetBulkBalancesTool,
    GetCurrentDateTimeTool,
    GetDocumentsTool,
    GetDocumentTool,
    GetPendingTransactionsTool,
    GetTransactionsTool,
    PayBeneficiariesTool,
    ResolveDateRangeTool,
    SendReportEmailTool,
    TransferFundsTool,
    create_banking_account_tools,
    create_banking_document_tools,
    create_banking_payment_tools,
    create_banking_tools,
    create_datetime_tools,
    create_reporting_tools,
)


class FakeBankingClient:
    def get_accounts(self) -> list[dict[str, Any]]:
        return []

    def get_balance(self, account_id: str) -> dict[str, Any]:
        return {"accountId": account_id}

    def get_transactions(
        self,
        account_id: str,
        from_date: str | None = None,
        to_date: str | None = None,
        transaction_type: str | None = None,
        include_pending: bool = False,
    ) -> list[dict[str, Any]]:
        _ = (account_id, from_date, to_date, transaction_type, include_pending)
        return []

    def get_pending_transactions(self, account_id: str) -> list[dict[str, Any]]:
        _ = account_id
        return []

    def transfer_funds(
        self,
        account_id: str,
        transfers: list[dict[str, Any]],
        profile_id: str | None = None,
    ) -> list[dict[str, Any]]:
        _ = (account_id, transfers, profile_id)
        return []

    def get_beneficiaries(self) -> list[dict[str, Any]]:
        return []

    def get_beneficiary_categories(self) -> list[dict[str, Any]]:
        return []

    def pay_beneficiaries(self, account_id: str, payments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        _ = (account_id, payments)
        return []

    def get_documents(self, account_id: str, from_date: str, to_date: str) -> list[dict[str, Any]]:
        _ = (account_id, from_date, to_date)
        return []

    def get_document(self, account_id: str, document_type: str, document_date: str) -> Any:
        _ = (account_id, document_type, document_date)
        return b""


class FakeEmailService:
    def send_report(self, subject: str, body: str) -> None:
        _ = (subject, body)


class FakeReportRepository(ReportRepository):
    def __init__(self) -> None:
        self.saved_reports: list[Any] = []

    def save(self, report):
        self.saved_reports.append(report)
        return report


def accepts_banking_client(client: BankingClient) -> BankingClient:
    return client


def accepts_email_service(service: EmailService) -> EmailService:
    return service


def test_fake_banking_client_satisfies_protocol():
    client = FakeBankingClient()

    assert accepts_banking_client(client) is client


def test_fake_email_service_satisfies_protocol():
    service = FakeEmailService()

    assert accepts_email_service(service) is service


def test_create_banking_account_tools_returns_account_tools_with_shared_client():
    banking_client = FakeBankingClient()

    tools = create_banking_account_tools(banking_client)

    assert [type(tool) for tool in tools] == [
        GetAccountsTool,
        GetBalanceTool,
        GetBulkBalancesTool,
        GetTransactionsTool,
        GetPendingTransactionsTool,
    ]
    assert all(tool._banking_client is banking_client for tool in tools)


def test_create_banking_document_tools_returns_document_tools_with_shared_client():
    banking_client = FakeBankingClient()

    tools = create_banking_document_tools(banking_client)

    assert [type(tool) for tool in tools] == [
        GetDocumentsTool,
        GetDocumentTool,
    ]
    assert all(tool._banking_client is banking_client for tool in tools)


def test_create_banking_payment_tools_returns_payment_tools_with_shared_client():
    banking_client = FakeBankingClient()

    tools = create_banking_payment_tools(banking_client)

    assert [type(tool) for tool in tools] == [
        TransferFundsTool,
        GetBeneficiariesTool,
        GetBeneficiaryCategoriesTool,
        PayBeneficiariesTool,
    ]
    assert all(tool._banking_client is banking_client for tool in tools)


def test_create_banking_tools_combines_all_grouped_factories():
    banking_client = FakeBankingClient()

    tools = create_banking_tools(banking_client)

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


def test_create_datetime_tools_returns_datetime_tools():
    tools = create_datetime_tools()

    assert [type(tool) for tool in tools] == [
        GetCurrentDateTimeTool,
        ResolveDateRangeTool,
    ]
    assert [tool.name for tool in tools] == [
        "get_current_datetime",
        "resolve_date_range",
    ]


def test_create_reporting_tools_returns_reporting_tool_with_shared_dependencies():
    email_service = FakeEmailService()
    report_repository = FakeReportRepository()

    tools = create_reporting_tools(email_service, report_repository)

    assert [type(tool) for tool in tools] == [SendReportEmailTool]
    assert tools[0]._email_service is email_service
    assert tools[0]._report_repository is report_repository
