import asyncio
from typing import Any

from krabs_domain.contracts import BankingClient
from krabs_tools.schema.banking_accounts import (
    GetAccountsInput,
    GetBalanceInput,
    GetBulkBalancesInput,
    GetPendingTransactionsInput,
    GetTransactionsInput,
)


class GetAccountsTool:
    name = "get_accounts"
    description = "Get a list of bank accounts available to the authenticated user."
    input_schema = GetAccountsInput

    def __init__(self, banking_client: BankingClient) -> None:
        self._banking_client = banking_client

    async def run(self, input_data: GetAccountsInput) -> list[dict[str, Any]]:
        _ = input_data
        return self._banking_client.get_accounts()


class GetBalanceTool:
    name = "get_balance"
    description = "Get the current and available balance for exactly one bank account. Use get_bulk_balances instead when balances are needed for multiple accounts."
    input_schema = GetBalanceInput

    def __init__(self, banking_client: BankingClient) -> None:
        self._banking_client = banking_client

    async def run(self, input_data: GetBalanceInput) -> dict[str, Any]:
        return self._banking_client.get_balance(input_data.account_id)


class GetBulkBalancesTool:
    name = "get_bulk_balances"
    description = "Get the current and available balances for multiple bank accounts in one grouped call. Use this instead of calling get_balance repeatedly when the user asks for balances for all accounts or more than one account."
    input_schema = GetBulkBalancesInput

    def __init__(self, banking_client: BankingClient) -> None:
        self._banking_client = banking_client

    async def run(self, input_data: GetBulkBalancesInput) -> list[dict[str, Any]]:
        return await asyncio.gather(
            *[
                asyncio.to_thread(self._banking_client.get_balance, account_id)
                for account_id in input_data.account_ids
            ]
        )


class GetTransactionsTool:
    name = "get_transactions"
    description = "Get posted transactions for a bank account, optionally filtered by date range, transaction type, and pending inclusion."
    input_schema = GetTransactionsInput

    def __init__(self, banking_client: BankingClient) -> None:
        self._banking_client = banking_client

    async def run(self, input_data: GetTransactionsInput) -> list[dict[str, Any]]:
        return self._banking_client.get_transactions(
            account_id=input_data.account_id,
            from_date=input_data.from_date,
            to_date=input_data.to_date,
            transaction_type=input_data.transaction_type,
            include_pending=input_data.include_pending,
        )


class GetPendingTransactionsTool:
    name = "get_pending_transactions"
    description = "Get pending transactions for a bank account."
    input_schema = GetPendingTransactionsInput

    def __init__(self, banking_client: BankingClient) -> None:
        self._banking_client = banking_client

    async def run(self, input_data: GetPendingTransactionsInput) -> list[dict[str, Any]]:
        return self._banking_client.get_pending_transactions(input_data.account_id)
