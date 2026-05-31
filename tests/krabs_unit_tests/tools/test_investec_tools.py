import asyncio
from typing import Any

from krabs_tools.schema import (
    BeneficiaryPaymentInstruction,
    GetAccountsInput,
    GetBalanceInput,
    GetBeneficiariesInput,
    GetBeneficiaryCategoriesInput,
    GetBulkBalancesInput,
    GetDocumentInput,
    GetDocumentsInput,
    GetPendingTransactionsInput,
    GetTransactionsInput,
    PayBeneficiariesInput,
    TransferFundsInput,
    TransferInstruction,
)
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
)

ACCOUNT_ID = "account-123"


class FakeAccountsClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def get_accounts(self) -> list[dict[str, Any]]:
        self.calls.append(("get_accounts", (), {}))
        return [{"accountId": ACCOUNT_ID}]

    def get_balance(self, account_id: str) -> dict[str, Any]:
        self.calls.append(("get_balance", (account_id,), {}))
        return {"accountId": account_id, "availableBalance": 100}

    def get_transactions(
        self,
        *,
        account_id: str,
        from_date: str | None,
        to_date: str | None,
        transaction_type: str | None,
        include_pending: bool,
    ) -> list[dict[str, Any]]:
        kwargs = {
            "account_id": account_id,
            "from_date": from_date,
            "to_date": to_date,
            "transaction_type": transaction_type,
            "include_pending": include_pending,
        }
        self.calls.append(("get_transactions", (), kwargs))
        return [{"description": "Card purchase"}]

    def get_pending_transactions(self, account_id: str) -> list[dict[str, Any]]:
        self.calls.append(("get_pending_transactions", (account_id,), {}))
        return [{"status": "PENDING"}]


class FakeDocumentsClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def get_documents(self, *, account_id: str, from_date: str, to_date: str) -> list[dict[str, Any]]:
        kwargs = {"account_id": account_id, "from_date": from_date, "to_date": to_date}
        self.calls.append(("get_documents", (), kwargs))
        return [{"documentType": "STATEMENT"}]

    def get_document(self, *, account_id: str, document_type: str, document_date: str) -> bytes:
        kwargs = {
            "account_id": account_id,
            "document_type": document_type,
            "document_date": document_date,
        }
        self.calls.append(("get_document", (), kwargs))
        return b"pdf-bytes"


class FakePaymentsClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def transfer_funds(
        self,
        *,
        account_id: str,
        transfers: list[dict[str, Any]],
        profile_id: str | None,
    ) -> list[dict[str, Any]]:
        kwargs = {"account_id": account_id, "transfers": transfers, "profile_id": profile_id}
        self.calls.append(("transfer_funds", (), kwargs))
        return [{"Status": "PROCESSED"}]

    def get_beneficiaries(self) -> list[dict[str, Any]]:
        self.calls.append(("get_beneficiaries", (), {}))
        return [{"beneficiaryId": "beneficiary-123"}]

    def get_beneficiary_categories(self) -> list[dict[str, Any]]:
        self.calls.append(("get_beneficiary_categories", (), {}))
        return [{"id": "category-123"}]

    def pay_beneficiaries(
        self,
        *,
        account_id: str,
        payments: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        kwargs = {"account_id": account_id, "payments": payments}
        self.calls.append(("pay_beneficiaries", (), kwargs))
        return [{"Status": "PROCESSED"}]


class TestAccountTools:
    def test_get_accounts_returns_client_accounts(self):
        client = FakeAccountsClient()
        tool = GetAccountsTool(client)

        result = asyncio.run(tool.run(GetAccountsInput()))

        assert result == [{"accountId": ACCOUNT_ID}]
        assert client.calls == [("get_accounts", (), {})]

    def test_get_balance_passes_account_id(self):
        client = FakeAccountsClient()
        tool = GetBalanceTool(client)

        result = asyncio.run(tool.run(GetBalanceInput(account_id=ACCOUNT_ID)))

        assert result == {"accountId": ACCOUNT_ID, "availableBalance": 100}
        assert client.calls == [("get_balance", (ACCOUNT_ID,), {})]

    def test_get_bulk_balances_fetches_each_requested_account(self):
        client = FakeAccountsClient()
        tool = GetBulkBalancesTool(client)

        result = asyncio.run(tool.run(GetBulkBalancesInput(account_ids=["account-1", "account-2"])))

        assert result == [
            {"accountId": "account-1", "availableBalance": 100},
            {"accountId": "account-2", "availableBalance": 100},
        ]
        assert sorted(call[1][0] for call in client.calls) == ["account-1", "account-2"]

    def test_get_transactions_passes_all_filter_fields(self):
        client = FakeAccountsClient()
        tool = GetTransactionsTool(client)
        input_data = GetTransactionsInput(
            account_id=ACCOUNT_ID,
            from_date="2026-05-01",
            to_date="2026-05-31",
            transaction_type="CardPurchases",
            include_pending=True,
        )

        result = asyncio.run(tool.run(input_data))

        assert result == [{"description": "Card purchase"}]
        assert client.calls == [
            (
                "get_transactions",
                (),
                {
                    "account_id": ACCOUNT_ID,
                    "from_date": "2026-05-01",
                    "to_date": "2026-05-31",
                    "transaction_type": "CardPurchases",
                    "include_pending": True,
                },
            )
        ]

    def test_get_pending_transactions_passes_account_id(self):
        client = FakeAccountsClient()
        tool = GetPendingTransactionsTool(client)

        result = asyncio.run(tool.run(GetPendingTransactionsInput(account_id=ACCOUNT_ID)))

        assert result == [{"status": "PENDING"}]
        assert client.calls == [("get_pending_transactions", (ACCOUNT_ID,), {})]


class TestDocumentTools:
    def test_get_documents_passes_account_and_date_range(self):
        client = FakeDocumentsClient()
        tool = GetDocumentsTool(client)

        result = asyncio.run(
            tool.run(
                GetDocumentsInput(
                    account_id=ACCOUNT_ID,
                    from_date="2026-05-01",
                    to_date="2026-05-31",
                )
            )
        )

        assert result == [{"documentType": "STATEMENT"}]
        assert client.calls == [
            (
                "get_documents",
                (),
                {"account_id": ACCOUNT_ID, "from_date": "2026-05-01", "to_date": "2026-05-31"},
            )
        ]

    def test_get_document_passes_document_identifiers(self):
        client = FakeDocumentsClient()
        tool = GetDocumentTool(client)

        result = asyncio.run(
            tool.run(
                GetDocumentInput(
                    account_id=ACCOUNT_ID,
                    document_type="STATEMENT",
                    document_date="2026-05-31",
                )
            )
        )

        assert result == b"pdf-bytes"
        assert client.calls == [
            (
                "get_document",
                (),
                {
                    "account_id": ACCOUNT_ID,
                    "document_type": "STATEMENT",
                    "document_date": "2026-05-31",
                },
            )
        ]


class TestPaymentTools:
    def test_transfer_funds_passes_alias_serialized_transfers_and_profile_id(self):
        client = FakePaymentsClient()
        tool = TransferFundsTool(client)
        transfer = TransferInstruction(
            beneficiary_account_id="beneficiary-account-123",
            amount=250,
            my_reference="Rent",
            their_reference="May rent",
        )

        result = asyncio.run(
            tool.run(
                TransferFundsInput(
                    account_id=ACCOUNT_ID,
                    transfers=[transfer],
                    profile_id="profile-123",
                )
            )
        )

        assert result == [{"Status": "PROCESSED"}]
        assert client.calls == [
            (
                "transfer_funds",
                (),
                {
                    "account_id": ACCOUNT_ID,
                    "transfers": [
                        {
                            "beneficiaryAccountId": "beneficiary-account-123",
                            "amount": 250.0,
                            "myReference": "Rent",
                            "theirReference": "May rent",
                        }
                    ],
                    "profile_id": "profile-123",
                },
            )
        ]

    def test_get_beneficiaries_returns_client_beneficiaries(self):
        client = FakePaymentsClient()
        tool = GetBeneficiariesTool(client)

        result = asyncio.run(tool.run(GetBeneficiariesInput()))

        assert result == [{"beneficiaryId": "beneficiary-123"}]
        assert client.calls == [("get_beneficiaries", (), {})]

    def test_get_beneficiary_categories_returns_client_categories(self):
        client = FakePaymentsClient()
        tool = GetBeneficiaryCategoriesTool(client)

        result = asyncio.run(tool.run(GetBeneficiaryCategoriesInput()))

        assert result == [{"id": "category-123"}]
        assert client.calls == [("get_beneficiary_categories", (), {})]

    def test_pay_beneficiaries_passes_alias_serialized_payments(self):
        client = FakePaymentsClient()
        tool = PayBeneficiariesTool(client)
        payment = BeneficiaryPaymentInstruction(
            beneficiary_id="beneficiary-123",
            amount=500,
            my_reference="Invoice",
            their_reference="INV-001",
        )

        result = asyncio.run(
            tool.run(
                PayBeneficiariesInput(
                    account_id=ACCOUNT_ID,
                    payments=[payment],
                )
            )
        )

        assert result == [{"Status": "PROCESSED"}]
        assert client.calls == [
            (
                "pay_beneficiaries",
                (),
                {
                    "account_id": ACCOUNT_ID,
                    "payments": [
                        {
                            "beneficiaryId": "beneficiary-123",
                            "amount": 500.0,
                            "myReference": "Invoice",
                            "theirReference": "INV-001",
                        }
                    ],
                },
            )
        ]
