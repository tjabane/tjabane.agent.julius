from typing import Any

from krabs_services.finance.investec_client import InvestecAccountsClient
from krabs_tools.schema.investec_accounts import (
    GetAccountsInput,
    GetBalanceInput,
    GetPendingTransactionsInput,
    GetTransactionsInput,
)


class GetAccountsTool:
    name = "get_accounts"
    description = "Get a list of Investec accounts available to the authenticated user."
    input_schema = GetAccountsInput

    def __init__(self, accounts_client: InvestecAccountsClient) -> None:
        self._accounts_client = accounts_client

    async def run(self, input_data: GetAccountsInput) -> list[dict[str, Any]]:
        _ = input_data
        return self._accounts_client.get_accounts()


class GetBalanceTool:
    name = "get_balance"
    description = "Get the current and available balance for an Investec account."
    input_schema = GetBalanceInput

    def __init__(self, accounts_client: InvestecAccountsClient) -> None:
        self._accounts_client = accounts_client

    async def run(self, input_data: GetBalanceInput) -> dict[str, Any]:
        return self._accounts_client.get_balance(input_data.account_id)


class GetTransactionsTool:
    name = "get_transactions"
    description = "Get posted transactions for an Investec account, optionally filtered by date range, transaction type, and pending inclusion."
    input_schema = GetTransactionsInput

    def __init__(self, accounts_client: InvestecAccountsClient) -> None:
        self._accounts_client = accounts_client

    async def run(self, input_data: GetTransactionsInput) -> list[dict[str, Any]]:
        return self._accounts_client.get_transactions(
            account_id=input_data.account_id,
            from_date=input_data.from_date,
            to_date=input_data.to_date,
            transaction_type=input_data.transaction_type,
            include_pending=input_data.include_pending,
        )


class GetPendingTransactionsTool:
    name = "get_pending_transactions"
    description = "Get pending transactions for an Investec account."
    input_schema = GetPendingTransactionsInput

    def __init__(self, accounts_client: InvestecAccountsClient) -> None:
        self._accounts_client = accounts_client

    async def run(self, input_data: GetPendingTransactionsInput) -> list[dict[str, Any]]:
        return self._accounts_client.get_pending_transactions(input_data.account_id)
