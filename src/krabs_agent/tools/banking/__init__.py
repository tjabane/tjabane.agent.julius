from __future__ import annotations
from typing import TYPE_CHECKING
from krabs_services.finance.investec_client import InvestecClient

if TYPE_CHECKING:
    from krabs_agent.tools.deps import ToolDeps

_investec: InvestecClient | None = None


def _get_investec() -> InvestecClient:
    global _investec
    if _investec is None:
        _investec = InvestecClient()
    return _investec


DEFINITIONS = [
    {
        "name": "get_accounts",
        "description": "List all Investec accounts with their IDs, names, and product types.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_balance",
        "description": "Get the current, available, and cash balance for a specific account.",
        "input_schema": {
            "type": "object",
            "properties": {"account_id": {"type": "string", "description": "The account ID"}},
            "required": ["account_id"],
        },
    },
    {
        "name": "get_transactions",
        "description": "Get transactions for an account. Optionally filter by date range and type.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "from_date": {"type": "string", "description": "YYYY-MM-DD"},
                "to_date": {"type": "string", "description": "YYYY-MM-DD"},
                "transaction_type": {"type": "string"},
                "include_pending": {"type": "boolean", "default": False},
            },
            "required": ["account_id"],
        },
    },
    {
        "name": "transfer_funds",
        "description": "Transfer funds to one or more Investec accounts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "Source account ID"},
                "transfers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "beneficiaryAccountId": {"type": "string"},
                            "amount": {"type": "number"},
                            "myReference": {"type": "string"},
                            "theirReference": {"type": "string"},
                        },
                        "required": ["beneficiaryAccountId", "amount", "myReference", "theirReference"],
                    },
                },
            },
            "required": ["account_id", "transfers"],
        },
    },
    {
        "name": "get_beneficiaries",
        "description": "List all saved beneficiaries and their categories.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "pay_beneficiary",
        "description": "Pay one or more beneficiaries from an account.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "payments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "beneficiaryId": {"type": "string"},
                            "amount": {"type": "number"},
                            "myReference": {"type": "string"},
                            "theirReference": {"type": "string"},
                        },
                        "required": ["beneficiaryId", "amount", "myReference", "theirReference"],
                    },
                },
            },
            "required": ["account_id", "payments"],
        },
    },
    {
        "name": "get_documents",
        "description": "List or retrieve statements and tax certificates for an account.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "from_date": {"type": "string", "description": "YYYY-MM-DD"},
                "to_date": {"type": "string", "description": "YYYY-MM-DD"},
                "document_type": {"type": "string", "description": "If provided, retrieves this specific document"},
                "document_date": {"type": "string", "description": "Required if document_type is provided"},
            },
            "required": ["account_id", "from_date", "to_date"],
        },
    },
]


def handle(tool_name: str, inputs: dict, deps: ToolDeps | None = None) -> str:
    investec = (deps.investec if deps and deps.investec else None) or _get_investec()

    if tool_name == "get_accounts":
        return str(investec.get_accounts())

    if tool_name == "get_balance":
        return str(investec.get_balance(inputs["account_id"]))

    if tool_name == "get_transactions":
        return str(investec.get_transactions(
            inputs["account_id"],
            from_date=inputs.get("from_date"),
            to_date=inputs.get("to_date"),
            transaction_type=inputs.get("transaction_type"),
            include_pending=inputs.get("include_pending", False),
        ))

    if tool_name == "transfer_funds":
        return str(investec.transfer_funds(inputs["account_id"], inputs["transfers"]))

    if tool_name == "get_beneficiaries":
        return str({
            "beneficiaries": investec.get_beneficiaries(),
            "categories": investec.get_beneficiary_categories(),
        })

    if tool_name == "pay_beneficiary":
        return str(investec.pay_beneficiaries(inputs["account_id"], inputs["payments"]))

    if tool_name == "get_documents":
        if "document_type" in inputs:
            return str(investec.get_document(inputs["account_id"], inputs["document_type"], inputs["document_date"]))
        return str(investec.get_documents(inputs["account_id"], inputs["from_date"], inputs["to_date"]))

    raise ValueError(f"Unknown banking tool: {tool_name}")
