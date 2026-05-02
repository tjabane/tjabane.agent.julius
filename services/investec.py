from datetime import datetime, timedelta, timezone
from typing import Any
import httpx
import os


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InvestecClient:
    _SANDBOX_BASE = "https://openapisandbox.investec.com"
    _PROD_BASE = "https://openapi.investec.com"

    def __init__(self):
        self._client_id = os.environ["INVESTEC_CLIENT_ID"]
        self._client_secret = os.environ["INVESTEC_CLIENT_SECRET"]
        self._api_key = os.environ["INVESTEC_API_KEY"]
        self._sandbox = os.environ.get("INVESTEC_SANDBOX", "true").lower() == "true"
        self._base = self._SANDBOX_BASE if self._sandbox else self._PROD_BASE
        self._token: str | None = None
        self._token_expires_at: datetime = _utcnow()

    def _ensure_token(self) -> None:
        if self._token and _utcnow() < self._token_expires_at:
            return
        url = f"{self._base}/identity/v2/oauth2/token"
        resp = httpx.post(
            url,
            data={"grant_type": "client_credentials", "scope": "accounts balances transactions transfers beneficiarypayments documents.statements documents.taxcertificates"},
            auth=(self._client_id, self._client_secret),
            headers={"x-api-key": self._api_key},
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expires_at = _utcnow() + timedelta(seconds=data["expires_in"] - 60)

    def _get(self, path: str, params: dict | None = None) -> Any:
        self._ensure_token()
        resp = httpx.get(
            f"{self._base}{path}",
            params=params,
            headers={"Authorization": f"Bearer {self._token}", "x-api-key": self._api_key},
        )
        resp.raise_for_status()
        return resp.json().get("data", resp.json())

    def _post(self, path: str, body: dict) -> Any:
        self._ensure_token()
        resp = httpx.post(
            f"{self._base}{path}",
            json=body,
            headers={"Authorization": f"Bearer {self._token}", "x-api-key": self._api_key},
        )
        resp.raise_for_status()
        return resp.json().get("data", resp.json())

    def get_accounts(self) -> list[dict]:
        return self._get("/za/pb/v1/accounts").get("accounts", [])

    def get_balance(self, account_id: str) -> dict:
        return self._get(f"/za/pb/v1/accounts/{account_id}/balance")

    def get_transactions(self, account_id: str, from_date: str | None = None, to_date: str | None = None, transaction_type: str | None = None, include_pending: bool = False) -> list[dict]:
        params = {"includePending": str(include_pending).lower()}
        if from_date:
            params["fromDate"] = from_date
        if to_date:
            params["toDate"] = to_date
        if transaction_type:
            params["transactionType"] = transaction_type
        return self._get(f"/za/pb/v1/accounts/{account_id}/transactions", params).get("transactions", [])

    def get_pending_transactions(self, account_id: str) -> list[dict]:
        return self._get(f"/za/pb/v1/accounts/{account_id}/pending-transactions").get("transactions", [])

    def transfer_funds(self, account_id: str, transfers: list[dict], profile_id: str | None = None) -> list[dict]:
        body: dict = {"transferList": transfers}
        if profile_id:
            body["profileId"] = profile_id
        return self._post(f"/za/pb/v1/accounts/{account_id}/transfermultiple", body).get("TransferResponses", [])

    def get_beneficiaries(self) -> list[dict]:
        return self._get("/za/pb/v1/accounts/beneficiaries")

    def get_beneficiary_categories(self) -> list[dict]:
        return self._get("/za/pb/v1/accounts/beneficiarycategories")

    def pay_beneficiaries(self, account_id: str, payments: list[dict]) -> list[dict]:
        return self._post(f"/za/pb/v1/accounts/{account_id}/paymultiple", {"paymentList": payments}).get("TransferResponses", [])

    def get_documents(self, account_id: str, from_date: str, to_date: str) -> list[dict]:
        result = self._get(f"/za/pb/v1/accounts/{account_id}/documents", {"fromDate": from_date, "toDate": to_date})
        return result if isinstance(result, list) else result.get("data", [])

    def get_document(self, account_id: str, document_type: str, document_date: str) -> Any:
        return self._get(f"/za/pb/v1/accounts/{account_id}/document/{document_type}/{document_date}")
