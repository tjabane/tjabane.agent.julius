from typing import Any

from krabs_services.finance.investec_client import InvestecAccountsClient
from krabs_tools.schema.investec_accounts import GetAccountsInput


class GetAccountsTool:
    name = "get_accounts"
    description = "Get a list of Investec accounts available to the authenticated user."
    input_schema = GetAccountsInput

    def __init__(self, accounts_client: InvestecAccountsClient) -> None:
        self._accounts_client = accounts_client

    async def run(self, input_data: GetAccountsInput) -> list[dict[str, Any]]:
        _ = input_data
        return self._accounts_client.get_accounts()
