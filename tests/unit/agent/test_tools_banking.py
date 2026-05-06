import pytest
from unittest.mock import MagicMock
from agent.tools import dispatch
from agent.tools.deps import ToolDeps


class TestDispatch:
    def test_routes_to_correct_handler(self):
        mock_investec = MagicMock()
        mock_investec.get_accounts.return_value = []
        deps = ToolDeps(investec=mock_investec)

        dispatch("get_accounts", {}, deps)

        mock_investec.get_accounts.assert_called_once()

    def test_raises_for_unknown_tool(self):
        with pytest.raises(ValueError, match="No handler for tool"):
            dispatch("nonexistent_tool", {})


class TestBankingTools:
    def test_get_accounts(self):
        mock_investec = MagicMock()
        mock_investec.get_accounts.return_value = [{"id": "123", "name": "Cheque"}]
        deps = ToolDeps(investec=mock_investec)

        result = dispatch("get_accounts", {}, deps)

        mock_investec.get_accounts.assert_called_once()
        assert "123" in result

    def test_get_balance(self):
        mock_investec = MagicMock()
        mock_investec.get_balance.return_value = {"current": 5000.0, "available": 4800.0}
        deps = ToolDeps(investec=mock_investec)

        result = dispatch("get_balance", {"account_id": "acc-1"}, deps)

        mock_investec.get_balance.assert_called_once_with("acc-1")
        assert "5000" in result

    def test_get_transactions_passes_all_filters(self):
        mock_investec = MagicMock()
        mock_investec.get_transactions.return_value = []
        deps = ToolDeps(investec=mock_investec)

        dispatch("get_transactions", {
            "account_id": "acc-1",
            "from_date": "2024-01-01",
            "to_date": "2024-01-31",
            "transaction_type": "DEBIT",
            "include_pending": True,
        }, deps)

        mock_investec.get_transactions.assert_called_once_with(
            "acc-1",
            from_date="2024-01-01",
            to_date="2024-01-31",
            transaction_type="DEBIT",
            include_pending=True,
        )

    def test_get_transactions_defaults_optional_filters(self):
        mock_investec = MagicMock()
        mock_investec.get_transactions.return_value = []
        deps = ToolDeps(investec=mock_investec)

        dispatch("get_transactions", {"account_id": "acc-1"}, deps)

        mock_investec.get_transactions.assert_called_once_with(
            "acc-1",
            from_date=None,
            to_date=None,
            transaction_type=None,
            include_pending=False,
        )

    def test_get_beneficiaries(self):
        mock_investec = MagicMock()
        mock_investec.get_beneficiaries.return_value = [{"beneficiaryId": "b1"}]
        mock_investec.get_beneficiary_categories.return_value = []
        deps = ToolDeps(investec=mock_investec)

        result = dispatch("get_beneficiaries", {}, deps)

        mock_investec.get_beneficiaries.assert_called_once()
        assert "b1" in result

    def test_get_documents_without_type(self):
        mock_investec = MagicMock()
        mock_investec.get_documents.return_value = []
        deps = ToolDeps(investec=mock_investec)

        dispatch("get_documents", {"account_id": "acc-1", "from_date": "2024-01-01", "to_date": "2024-03-31"}, deps)

        mock_investec.get_documents.assert_called_once_with("acc-1", "2024-01-01", "2024-03-31")

    def test_get_documents_with_type_calls_get_document(self):
        mock_investec = MagicMock()
        mock_investec.get_document.return_value = {"content": "..."}
        deps = ToolDeps(investec=mock_investec)

        dispatch("get_documents", {
            "account_id": "acc-1",
            "from_date": "2024-01-01",
            "to_date": "2024-03-31",
            "document_type": "statement",
            "document_date": "2024-02-01",
        }, deps)

        mock_investec.get_document.assert_called_once_with("acc-1", "statement", "2024-02-01")
