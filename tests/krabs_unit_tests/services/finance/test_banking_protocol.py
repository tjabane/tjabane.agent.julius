from __future__ import annotations

from krabs_domain.banking import BankingClient
from krabs_services.finance.investec_client import InvestecClient


def accepts_banking_client(client: BankingClient) -> BankingClient:
    return client


def test_investec_client_satisfies_banking_client_protocol() -> None:
    client = InvestecClient(
        client_id="client-id",
        client_secret="client-secret",
        api_key="api-key",
        base_url="https://example.test",
    )

    assert accepts_banking_client(client) is client
