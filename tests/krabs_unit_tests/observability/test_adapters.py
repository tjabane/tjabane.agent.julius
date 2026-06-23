from __future__ import annotations

from contextlib import contextmanager

from krabs_observability.adapters import BankingClient, MessageSender
from krabs_observability.semantic import AttributeName, SpanName


class StubMessageSender:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, str]] = []

    def send_message(self, to: str, body: str) -> None:
        self.sent_messages.append({"to": to, "body": body})


class StubBankingClient:
    def get_accounts(self) -> list[dict]:
        return [{"accountId": "private-account-id"}]

    def get_balance(self, account_id: str) -> dict:
        return {"accountId": account_id, "currentBalance": 1000}

    def get_transactions(
        self,
        account_id: str,
        from_date: str | None = None,
        to_date: str | None = None,
        transaction_type: str | None = None,
        include_pending: bool = False,
    ) -> list[dict]:
        return [{"description": "private transaction"}]

    def get_pending_transactions(self, account_id: str) -> list[dict]:
        return []

    def transfer_funds(
        self,
        account_id: str,
        transfers: list[dict],
        profile_id: str | None = None,
    ) -> list[dict]:
        return []

    def get_beneficiaries(self) -> list[dict]:
        return []

    def get_beneficiary_categories(self) -> list[dict]:
        return []

    def pay_beneficiaries(self, account_id: str, payments: list[dict]) -> list[dict]:
        return []

    def get_documents(self, account_id: str, from_date: str, to_date: str) -> list[dict]:
        return []

    def get_document(self, account_id: str, document_type: str, document_date: str):
        return {}


def test_message_sender_adapter_traces_twilio_send_without_message_payload(monkeypatch) -> None:
    spans = []

    @contextmanager
    def fake_trace_operation(span_name, *, attributes, allowed_attribute_names):
        spans.append(
            {
                "span_name": span_name,
                "attributes": attributes,
                "allowed_attribute_names": allowed_attribute_names,
            }
        )
        yield

    monkeypatch.setattr("krabs_observability.adapters.trace_operation", fake_trace_operation)
    sender = StubMessageSender()
    adapter = MessageSender(sender)

    adapter.send_message(to="+27829876543", body="Your balance is private")

    assert sender.sent_messages == [{"to": "+27829876543", "body": "Your balance is private"}]
    assert spans[0]["span_name"] == SpanName.TWILIO_SEND
    assert spans[0]["attributes"] == {
        AttributeName.DEPENDENCY_NAME: "twilio",
        AttributeName.MESSAGING_PROVIDER: "twilio",
        AttributeName.OPERATION_NAME: "message.send",
    }


def test_banking_adapter_traces_investec_operation_without_banking_payload(monkeypatch) -> None:
    spans = []

    @contextmanager
    def fake_trace_operation(span_name, *, attributes, allowed_attribute_names):
        spans.append(
            {
                "span_name": span_name,
                "attributes": attributes,
                "allowed_attribute_names": allowed_attribute_names,
            }
        )
        yield

    monkeypatch.setattr("krabs_observability.adapters.trace_operation", fake_trace_operation)
    adapter = BankingClient(StubBankingClient())

    assert adapter.get_balance("private-account-id")["currentBalance"] == 1000

    assert spans[0]["span_name"] == SpanName.INVESTEC_OPERATION
    assert spans[0]["attributes"] == {
        AttributeName.DEPENDENCY_NAME: "investec",
        AttributeName.OPERATION_NAME: "balance.get",
    }
