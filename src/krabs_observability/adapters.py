from __future__ import annotations

from typing import Any, Protocol

from krabs_domain.contracts import BankingClient as BankingClientProtocol
from krabs_observability.semantic import AttributeName, SpanName
from krabs_observability.telemetry import trace_operation

_DEPENDENCY_ATTRS = {
    AttributeName.DEPENDENCY_NAME,
    AttributeName.OPERATION_NAME,
    AttributeName.MESSAGING_PROVIDER,
}


class MessageSenderProtocol(Protocol):
    def send_message(self, to: str, body: str) -> None: ...


class MessageSender:
    def __init__(self, inner: MessageSenderProtocol) -> None:
        self._inner = inner

    def send_message(self, to: str, body: str) -> None:
        with trace_operation(
            SpanName.TWILIO_SEND,
            attributes={
                AttributeName.DEPENDENCY_NAME: "twilio",
                AttributeName.MESSAGING_PROVIDER: "twilio",
                AttributeName.OPERATION_NAME: "message.send",
            },
            allowed_attribute_names=_DEPENDENCY_ATTRS,
        ):
            self._inner.send_message(to=to, body=body)


class BankingClient:
    def __init__(self, inner: BankingClientProtocol) -> None:
        self._inner = inner

    def get_accounts(self) -> list[dict[str, Any]]:
        return self._trace("accounts.get", lambda: self._inner.get_accounts())

    def get_balance(self, account_id: str) -> dict[str, Any]:
        return self._trace("balance.get", lambda: self._inner.get_balance(account_id))

    def get_transactions(
        self,
        account_id: str,
        from_date: str | None = None,
        to_date: str | None = None,
        transaction_type: str | None = None,
        include_pending: bool = False,
    ) -> list[dict[str, Any]]:
        return self._trace(
            "transactions.get",
            lambda: self._inner.get_transactions(
                account_id=account_id,
                from_date=from_date,
                to_date=to_date,
                transaction_type=transaction_type,
                include_pending=include_pending,
            ),
        )

    def get_pending_transactions(self, account_id: str) -> list[dict[str, Any]]:
        return self._trace("pending_transactions.get", lambda: self._inner.get_pending_transactions(account_id))

    def transfer_funds(
        self,
        account_id: str,
        transfers: list[dict[str, Any]],
        profile_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return self._trace(
            "funds.transfer",
            lambda: self._inner.transfer_funds(account_id=account_id, transfers=transfers, profile_id=profile_id),
        )

    def get_beneficiaries(self) -> list[dict[str, Any]]:
        return self._trace("beneficiaries.get", lambda: self._inner.get_beneficiaries())

    def get_beneficiary_categories(self) -> list[dict[str, Any]]:
        return self._trace("beneficiary_categories.get", lambda: self._inner.get_beneficiary_categories())

    def pay_beneficiaries(self, account_id: str, payments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return self._trace(
            "beneficiaries.pay",
            lambda: self._inner.pay_beneficiaries(account_id=account_id, payments=payments),
        )

    def get_documents(self, account_id: str, from_date: str, to_date: str) -> list[dict[str, Any]]:
        return self._trace(
            "documents.get",
            lambda: self._inner.get_documents(account_id=account_id, from_date=from_date, to_date=to_date),
        )

    def get_document(self, account_id: str, document_type: str, document_date: str) -> Any:
        return self._trace(
            "document.get",
            lambda: self._inner.get_document(
                account_id=account_id,
                document_type=document_type,
                document_date=document_date,
            ),
        )

    def _trace(self, operation_name: str, call):
        with trace_operation(
            SpanName.INVESTEC_OPERATION,
            attributes={
                AttributeName.DEPENDENCY_NAME: "investec",
                AttributeName.OPERATION_NAME: operation_name,
            },
            allowed_attribute_names=_DEPENDENCY_ATTRS,
        ):
            return call()
