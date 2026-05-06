"""
Integration tests — hit the Investec sandbox API directly.

Run with:  pytest -m integration
Skip automatically if INVESTEC_CLIENT_ID is not set.
"""
import os
import pytest
from services.investec_client import InvestecClient

pytestmark = pytest.mark.integration

requires_credentials = pytest.mark.skipif(
    not os.environ.get("INVESTEC_CLIENT_ID"),
    reason="Investec sandbox credentials not set",
)


@pytest.fixture(scope="module")
def client():
    return InvestecClient()


@pytest.fixture(scope="module")
def first_account(client):
    accounts = client.get_accounts()
    assert accounts, "Sandbox returned no accounts"
    return accounts[0]


# ── Auth ──────────────────────────────────────────────────────────────────────

@requires_credentials
def test_can_authenticate(client):
    client._ensure_token()
    assert client._token is not None
    assert len(client._token) > 0


# ── Accounts ──────────────────────────────────────────────────────────────────

@requires_credentials
def test_get_accounts_returns_list(client):
    accounts = client.get_accounts()
    assert isinstance(accounts, list)
    assert len(accounts) > 0


@requires_credentials
def test_account_has_required_fields(first_account):
    assert "accountId" in first_account
    assert "accountNumber" in first_account
    assert "productName" in first_account


# ── Balance ───────────────────────────────────────────────────────────────────

@requires_credentials
def test_get_balance_returns_data(client, first_account):
    balance = client.get_balance(first_account["accountId"])
    assert "currentBalance" in balance
    assert "availableBalance" in balance
    assert balance.get("currency") == "ZAR"


@requires_credentials
def test_balance_values_are_numeric(client, first_account):
    balance = client.get_balance(first_account["accountId"])
    assert isinstance(balance["currentBalance"], (int, float))
    assert isinstance(balance["availableBalance"], (int, float))


# ── Transactions ──────────────────────────────────────────────────────────────

@requires_credentials
def test_get_transactions_returns_list(client, first_account):
    transactions = client.get_transactions(first_account["accountId"])
    assert isinstance(transactions, list)


@requires_credentials
def test_transaction_has_required_fields(client, first_account):
    transactions = client.get_transactions(first_account["accountId"])
    if transactions:
        txn = transactions[0]
        assert "type" in txn
        assert "amount" in txn
        assert "description" in txn
        assert txn["type"] in ("CREDIT", "DEBIT")


@requires_credentials
def test_get_transactions_with_date_range(client, first_account):
    transactions = client.get_transactions(
        first_account["accountId"],
        from_date="2026-01-01",
        to_date="2026-04-30",
    )
    assert isinstance(transactions, list)


@requires_credentials
def test_get_pending_transactions(client, first_account):
    pending = client.get_pending_transactions(first_account["accountId"])
    assert isinstance(pending, list)


# ── Beneficiaries ─────────────────────────────────────────────────────────────

@requires_credentials
def test_get_beneficiaries_returns_list(client):
    beneficiaries = client.get_beneficiaries()
    assert isinstance(beneficiaries, list)


@requires_credentials
def test_get_beneficiary_categories_returns_list(client):
    categories = client.get_beneficiary_categories()
    assert isinstance(categories, list)


@requires_credentials
def test_beneficiary_category_has_required_fields(client):
    categories = client.get_beneficiary_categories()
    if categories:
        # Sandbox returns PascalCase fields
        assert "CategoryId" in categories[0]
        assert "CategoryName" in categories[0]


# ── Documents ─────────────────────────────────────────────────────────────────

@requires_credentials
def test_get_documents_returns_list(client, first_account):
    documents = client.get_documents(
        first_account["accountId"],
        from_date="2026-01-01",
        to_date="2026-04-30",
    )
    assert isinstance(documents, list)
