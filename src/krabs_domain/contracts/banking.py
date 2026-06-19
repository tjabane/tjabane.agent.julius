from __future__ import annotations

from typing import Any, Protocol


class BankingClient(Protocol):
    def get_accounts(self) -> list[dict[str, Any]]: ...

    def get_balance(self, account_id: str) -> dict[str, Any]: ...

    def get_transactions(
        self,
        account_id: str,
        from_date: str | None = None,
        to_date: str | None = None,
        transaction_type: str | None = None,
        include_pending: bool = False,
    ) -> list[dict[str, Any]]: ...

    def get_pending_transactions(self, account_id: str) -> list[dict[str, Any]]: ...

    def transfer_funds(
        self,
        account_id: str,
        transfers: list[dict[str, Any]],
        profile_id: str | None = None,
    ) -> list[dict[str, Any]]: ...

    def get_beneficiaries(self) -> list[dict[str, Any]]: ...

    def get_beneficiary_categories(self) -> list[dict[str, Any]]: ...

    def pay_beneficiaries(self, account_id: str, payments: list[dict[str, Any]]) -> list[dict[str, Any]]: ...

    def get_documents(self, account_id: str, from_date: str, to_date: str) -> list[dict[str, Any]]: ...

    def get_document(self, account_id: str, document_type: str, document_date: str) -> Any: ...
