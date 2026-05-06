from datetime import datetime, timedelta, timezone

def _utcnow():
    return datetime.now(timezone.utc)
from unittest.mock import MagicMock, patch
import pytest
from services.investec_client import InvestecClient

ACCOUNT_ID = "172878438332791809002"
SANDBOX_BASE = "https://openapisandbox.investec.com"


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.raise_for_status = MagicMock()
    return mock


def _token_response(expires_in: int = 1800) -> MagicMock:
    return _mock_response({"access_token": "mock-token", "expires_in": expires_in, "token_type": "Bearer"})


# ── Auth ──────────────────────────────────────────────────────────────────────

class TestEnsureToken:
    @patch("httpx.post")
    def test_fetches_token_on_first_call(self, mock_post):
        mock_post.return_value = _token_response()
        client = InvestecClient()
        client._ensure_token()

        assert client._token == "mock-token"
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert f"{SANDBOX_BASE}/identity/v2/oauth2/token" in call_kwargs.args[0]

    @patch("httpx.post")
    def test_does_not_refresh_valid_token(self, mock_post):
        mock_post.return_value = _token_response()
        client = InvestecClient()
        client._token = "existing-token"
        client._token_expires_at = _utcnow() + timedelta(minutes=10)

        client._ensure_token()

        mock_post.assert_not_called()
        assert client._token == "existing-token"

    @patch("httpx.post")
    def test_refreshes_expired_token(self, mock_post):
        mock_post.return_value = _token_response()
        client = InvestecClient()
        client._token = "old-token"
        client._token_expires_at = _utcnow() - timedelta(seconds=1)

        client._ensure_token()

        mock_post.assert_called_once()
        assert client._token == "mock-token"

    @patch("httpx.post")
    def test_token_expiry_has_60s_buffer(self, mock_post):
        mock_post.return_value = _token_response(expires_in=1800)
        client = InvestecClient()
        client._ensure_token()

        expected = _utcnow() + timedelta(seconds=1800 - 60)
        assert abs((client._token_expires_at - expected).total_seconds()) < 2

    @patch("httpx.post")
    def test_uses_sandbox_url(self, mock_post):
        mock_post.return_value = _token_response()
        client = InvestecClient()
        client._ensure_token()

        url = mock_post.call_args.args[0]
        assert SANDBOX_BASE in url

    @patch("httpx.post")
    def test_sends_api_key_header(self, mock_post):
        mock_post.return_value = _token_response()
        client = InvestecClient()
        client._ensure_token()

        headers = mock_post.call_args.kwargs.get("headers", {})
        assert headers.get("x-api-key") == "test-api-key"


# ── Accounts ──────────────────────────────────────────────────────────────────

class TestGetAccounts:
    @patch("httpx.get")
    @patch("httpx.post")
    def test_returns_accounts_list(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.return_value = _mock_response({
            "data": {
                "accounts": [
                    {"accountId": ACCOUNT_ID, "accountName": "Mr J Smith", "productName": "Private Bank Account"}
                ]
            }
        })
        client = InvestecClient()
        result = client.get_accounts()

        assert len(result) == 1
        assert result[0]["accountId"] == ACCOUNT_ID

    @patch("httpx.get")
    @patch("httpx.post")
    def test_returns_empty_list_when_no_accounts(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.return_value = _mock_response({"data": {}})
        client = InvestecClient()

        assert client.get_accounts() == []

    @patch("httpx.get")
    @patch("httpx.post")
    def test_calls_correct_endpoint(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.return_value = _mock_response({"data": {"accounts": []}})
        client = InvestecClient()
        client.get_accounts()

        url = mock_get.call_args.args[0]
        assert url == f"{SANDBOX_BASE}/za/pb/v1/accounts"


# ── Balance ───────────────────────────────────────────────────────────────────

class TestGetBalance:
    @patch("httpx.get")
    @patch("httpx.post")
    def test_returns_balance_data(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.return_value = _mock_response({
            "data": {
                "accountId": ACCOUNT_ID,
                "currentBalance": 28857.76,
                "availableBalance": 98857.76,
                "currency": "ZAR",
            }
        })
        client = InvestecClient()
        result = client.get_balance(ACCOUNT_ID)

        assert result["currentBalance"] == 28857.76
        assert result["currency"] == "ZAR"

    @patch("httpx.get")
    @patch("httpx.post")
    def test_calls_correct_endpoint(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.return_value = _mock_response({"data": {}})
        client = InvestecClient()
        client.get_balance(ACCOUNT_ID)

        url = mock_get.call_args.args[0]
        assert url == f"{SANDBOX_BASE}/za/pb/v1/accounts/{ACCOUNT_ID}/balance"


# ── Transactions ──────────────────────────────────────────────────────────────

class TestGetTransactions:
    @patch("httpx.get")
    @patch("httpx.post")
    def test_returns_transactions(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.return_value = _mock_response({
            "data": {
                "transactions": [
                    {"type": "DEBIT", "amount": 150.00, "description": "WOOLWORTHS FOOD", "status": "POSTED"}
                ]
            }
        })
        client = InvestecClient()
        result = client.get_transactions(ACCOUNT_ID)

        assert len(result) == 1
        assert result[0]["description"] == "WOOLWORTHS FOOD"

    @patch("httpx.get")
    @patch("httpx.post")
    def test_passes_date_range_params(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.return_value = _mock_response({"data": {"transactions": []}})
        client = InvestecClient()
        client.get_transactions(ACCOUNT_ID, from_date="2026-01-01", to_date="2026-01-31")

        params = mock_get.call_args.kwargs.get("params", {})
        assert params["fromDate"] == "2026-01-01"
        assert params["toDate"] == "2026-01-31"

    @patch("httpx.get")
    @patch("httpx.post")
    def test_passes_transaction_type_param(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.return_value = _mock_response({"data": {"transactions": []}})
        client = InvestecClient()
        client.get_transactions(ACCOUNT_ID, transaction_type="CardPurchases")

        params = mock_get.call_args.kwargs.get("params", {})
        assert params["transactionType"] == "CardPurchases"

    @patch("httpx.get")
    @patch("httpx.post")
    def test_include_pending_defaults_false(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.return_value = _mock_response({"data": {"transactions": []}})
        client = InvestecClient()
        client.get_transactions(ACCOUNT_ID)

        params = mock_get.call_args.kwargs.get("params", {})
        assert params["includePending"] == "false"

    @patch("httpx.get")
    @patch("httpx.post")
    def test_include_pending_true(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.return_value = _mock_response({"data": {"transactions": []}})
        client = InvestecClient()
        client.get_transactions(ACCOUNT_ID, include_pending=True)

        params = mock_get.call_args.kwargs.get("params", {})
        assert params["includePending"] == "true"

    @patch("httpx.get")
    @patch("httpx.post")
    def test_omits_optional_params_when_not_provided(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.return_value = _mock_response({"data": {"transactions": []}})
        client = InvestecClient()
        client.get_transactions(ACCOUNT_ID)

        params = mock_get.call_args.kwargs.get("params", {})
        assert "fromDate" not in params
        assert "toDate" not in params
        assert "transactionType" not in params


# ── Transfers ─────────────────────────────────────────────────────────────────

class TestTransferFunds:
    @patch("httpx.post")
    def test_returns_transfer_responses(self, mock_post):
        mock_post.side_effect = [
            _token_response(),
            _mock_response({
                "data": {
                    "TransferResponses": [
                        {"PaymentReferenceNumber": "REF001", "Status": "PROCESSED"}
                    ]
                }
            }),
        ]
        client = InvestecClient()
        transfers = [{"beneficiaryAccountId": "999", "amount": 500, "myReference": "Rent", "theirReference": "TJ"}]
        result = client.transfer_funds(ACCOUNT_ID, transfers)

        assert result[0]["Status"] == "PROCESSED"

    @patch("httpx.post")
    def test_body_includes_transfer_list(self, mock_post):
        mock_post.side_effect = [
            _token_response(),
            _mock_response({"data": {"TransferResponses": []}}),
        ]
        client = InvestecClient()
        transfers = [{"beneficiaryAccountId": "999", "amount": 100, "myReference": "A", "theirReference": "B"}]
        client.transfer_funds(ACCOUNT_ID, transfers)

        body = mock_post.call_args.kwargs.get("json", {})
        assert body["transferList"] == transfers

    @patch("httpx.post")
    def test_body_includes_profile_id_when_provided(self, mock_post):
        mock_post.side_effect = [
            _token_response(),
            _mock_response({"data": {"TransferResponses": []}}),
        ]
        client = InvestecClient()
        client.transfer_funds(ACCOUNT_ID, [], profile_id="profile-123")

        body = mock_post.call_args.kwargs.get("json", {})
        assert body["profileId"] == "profile-123"

    @patch("httpx.post")
    def test_body_excludes_profile_id_when_not_provided(self, mock_post):
        mock_post.side_effect = [
            _token_response(),
            _mock_response({"data": {"TransferResponses": []}}),
        ]
        client = InvestecClient()
        client.transfer_funds(ACCOUNT_ID, [])

        body = mock_post.call_args.kwargs.get("json", {})
        assert "profileId" not in body


# ── Beneficiaries ─────────────────────────────────────────────────────────────

class TestBeneficiaries:
    @patch("httpx.get")
    @patch("httpx.post")
    def test_get_beneficiaries_returns_list(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.return_value = _mock_response({
            "data": [{"beneficiaryId": "BEN001", "beneficiaryName": "ACME Ltd"}]
        })
        client = InvestecClient()
        result = client.get_beneficiaries()

        assert result[0]["beneficiaryId"] == "BEN001"

    @patch("httpx.get")
    @patch("httpx.post")
    def test_get_beneficiary_categories(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.return_value = _mock_response({
            "data": [{"id": "1", "name": "Personal", "isDefault": True}]
        })
        client = InvestecClient()
        result = client.get_beneficiary_categories()

        assert result[0]["name"] == "Personal"

    @patch("httpx.post")
    def test_pay_beneficiaries_sends_payment_list(self, mock_post):
        mock_post.side_effect = [
            _token_response(),
            _mock_response({"data": {"TransferResponses": [{"Status": "PROCESSED"}]}}),
        ]
        client = InvestecClient()
        payments = [{"beneficiaryId": "BEN001", "amount": 200, "myReference": "X", "theirReference": "Y"}]
        result = client.pay_beneficiaries(ACCOUNT_ID, payments)

        body = mock_post.call_args.kwargs.get("json", {})
        assert body["paymentList"] == payments
        assert result[0]["Status"] == "PROCESSED"


# ── Documents ─────────────────────────────────────────────────────────────────

class TestDocuments:
    @patch("httpx.get")
    @patch("httpx.post")
    def test_get_documents_passes_date_params(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.return_value = _mock_response({"data": {"data": []}})
        client = InvestecClient()
        client.get_documents(ACCOUNT_ID, "2026-01-01", "2026-01-31")

        params = mock_get.call_args.kwargs.get("params", {})
        assert params["fromDate"] == "2026-01-01"
        assert params["toDate"] == "2026-01-31"

    @patch("httpx.get")
    @patch("httpx.post")
    def test_get_document_calls_correct_endpoint(self, mock_post, mock_get):
        mock_post.return_value = _token_response()
        mock_get.return_value = _mock_response({"data": {}})
        client = InvestecClient()
        client.get_document(ACCOUNT_ID, "STATEMENT", "2026-01-31")

        url = mock_get.call_args.args[0]
        assert url == f"{SANDBOX_BASE}/za/pb/v1/accounts/{ACCOUNT_ID}/document/STATEMENT/2026-01-31"


# ── Error handling ────────────────────────────────────────────────────────────

class TestErrorHandling:
    @patch("httpx.post")
    def test_raises_on_auth_failure(self, mock_post):
        from httpx import HTTPStatusError, Request, Response
        mock_post.return_value = MagicMock(
            raise_for_status=MagicMock(
                side_effect=HTTPStatusError("401", request=MagicMock(), response=MagicMock())
            )
        )
        client = InvestecClient()
        with pytest.raises(Exception):
            client._ensure_token()

    @patch("httpx.get")
    @patch("httpx.post")
    def test_raises_on_api_error(self, mock_post, mock_get):
        from httpx import HTTPStatusError
        mock_post.return_value = _token_response()
        mock_get.return_value = MagicMock(
            raise_for_status=MagicMock(
                side_effect=HTTPStatusError("500", request=MagicMock(), response=MagicMock())
            )
        )
        client = InvestecClient()
        with pytest.raises(Exception):
            client.get_accounts()
