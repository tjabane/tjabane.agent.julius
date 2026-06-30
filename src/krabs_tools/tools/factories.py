from collections.abc import Callable

from krabs_domain.contracts import BankingClient, EmailService
from krabs_domain.repositories.reporting import ReportRepository
from krabs_tools.registry import Tool
from krabs_tools.tools.banking import (
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
)
from krabs_tools.tools.datetime import GetCurrentDateTimeTool, ResolveDateRangeTool
from krabs_tools.tools.reporting import SendReportEmailTool


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


def create_readonly_banking_tools(banking_client: BankingClient) -> list[Tool]:
    return [
        *create_banking_account_tools(banking_client),
        *create_banking_document_tools(banking_client),
    ]


def create_banking_tools(banking_client: BankingClient) -> list[Tool]:
    return [
        *create_readonly_banking_tools(banking_client),
        *create_banking_payment_tools(banking_client),
    ]


def create_datetime_tools() -> list[Tool]:
    return [
        GetCurrentDateTimeTool(),
        ResolveDateRangeTool(),
    ]


def create_reporting_tools(
    email_service: EmailService,
    report_repository: ReportRepository | Callable[[], ReportRepository],
) -> list[Tool]:
    return [
        SendReportEmailTool(email_service, report_repository),
    ]
