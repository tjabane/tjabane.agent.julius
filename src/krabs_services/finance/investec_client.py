import os
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx


def _utcnow() -> datetime:
    return datetime.now(UTC)


def get_investec_base_url() -> str:
    sandbox = os.environ.get("INVESTEC_SANDBOX", "true").lower() == "true"
    default_url_key = "INVESTEC_SANDBOX_URL" if sandbox else "INVESTEC_PROD_URL"
    return os.environ[default_url_key].rstrip("/")


def get_investec_timeout_seconds() -> float:
    return float(os.environ["INVESTEC_TIMEOUT_SECONDS"])


class InvestecHttpClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        api_key: str,
        base_url: str,
        timeout: float,
    ):
        self._client_id = client_id
        self._client_secret = client_secret
        self._api_key = api_key
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self._token: str | None = None
        self._token_expires_at: datetime = _utcnow()

    def _ensure_token(self) -> None:
        if self._token and _utcnow() < self._token_expires_at:
            return
        url = f"{self._base}/identity/v2/oauth2/token"
        resp = httpx.post(
            url,
            data={
                "grant_type": "client_credentials",
                "scope": "accounts balances transactions transfers beneficiarypayments documents.statements documents.taxcertificates",
            },
            auth=(self._client_id, self._client_secret),
            headers={"x-api-key": self._api_key},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expires_at = _utcnow() + timedelta(seconds=data["expires_in"] - 60)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        self._ensure_token()
        resp = httpx.get(
            f"{self._base}{path}",
            params=params,
            headers={"Authorization": f"Bearer {self._token}", "x-api-key": self._api_key},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        response_body = resp.json()
        return response_body.get("data", response_body)

    def _post(self, path: str, body: dict[str, Any]) -> Any:
        self._ensure_token()
        resp = httpx.post(
            f"{self._base}{path}",
            json=body,
            headers={"Authorization": f"Bearer {self._token}", "x-api-key": self._api_key},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        response_body = resp.json()
        return response_body.get("data", response_body)


class InvestecAccountsClient:
    def __init__(self, http_client: InvestecHttpClient):
        self._http_client = http_client

    def get_accounts(self) -> list[dict[str, Any]]:
        return self._http_client._get("/za/pb/v1/accounts").get("accounts", [])

    def get_balance(self, account_id: str) -> dict[str, Any]:
        return self._http_client._get(f"/za/pb/v1/accounts/{account_id}/balance")

    def get_transactions(
        self,
        account_id: str,
        from_date: str | None = None,
        to_date: str | None = None,
        transaction_type: str | None = None,
        include_pending: bool = False,
    ) -> list[dict[str, Any]]:
        params = {"includePending": str(include_pending).lower()}
        if from_date:
            params["fromDate"] = from_date
        if to_date:
            params["toDate"] = to_date
        if transaction_type:
            params["transactionType"] = transaction_type
        return self._http_client._get(f"/za/pb/v1/accounts/{account_id}/transactions", params).get("transactions", [])

    def get_pending_transactions(self, account_id: str) -> list[dict[str, Any]]:
        return self._http_client._get(f"/za/pb/v1/accounts/{account_id}/pending-transactions").get("transactions", [])


class InvestecPaymentsClient:
    def __init__(self, http_client: InvestecHttpClient):
        self._http_client = http_client

    def transfer_funds(
        self,
        account_id: str,
        transfers: list[dict[str, Any]],
        profile_id: str | None = None,
    ) -> list[dict[str, Any]]:
        body: dict[str, Any] = {"transferList": transfers}
        if profile_id:
            body["profileId"] = profile_id
        return self._http_client._post(f"/za/pb/v1/accounts/{account_id}/transfermultiple", body).get(
            "TransferResponses", []
        )

    def get_beneficiaries(self) -> list[dict[str, Any]]:
        return self._http_client._get("/za/pb/v1/accounts/beneficiaries")

    def get_beneficiary_categories(self) -> list[dict[str, Any]]:
        return self._http_client._get("/za/pb/v1/accounts/beneficiarycategories")

    def pay_beneficiaries(self, account_id: str, payments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return self._http_client._post(f"/za/pb/v1/accounts/{account_id}/paymultiple", {"paymentList": payments}).get(
            "TransferResponses", []
        )


class InvestecDocumentsClient:
    def __init__(self, http_client: InvestecHttpClient):
        self._http_client = http_client

    def get_documents(self, account_id: str, from_date: str, to_date: str) -> list[dict[str, Any]]:
        result = self._http_client._get(
            f"/za/pb/v1/accounts/{account_id}/documents", {"fromDate": from_date, "toDate": to_date}
        )
        return result if isinstance(result, list) else result.get("data", [])

    def get_document(self, account_id: str, document_type: str, document_date: str) -> Any:
        return self._http_client._get(f"/za/pb/v1/accounts/{account_id}/document/{document_type}/{document_date}")


class InvestecClient:
    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        http_client: InvestecHttpClient | None = None,
    ):
        client_id = client_id or os.environ["INVESTEC_CLIENT_ID"]
        client_secret = client_secret or os.environ["INVESTEC_CLIENT_SECRET"]
        api_key = api_key or os.environ["INVESTEC_API_KEY"]
        base_url = base_url or os.environ.get("INVESTEC_BASE_URL") or get_investec_base_url()
        timeout = timeout if timeout is not None else get_investec_timeout_seconds()
        self._http_client = http_client or InvestecHttpClient(
            client_id=client_id,
            client_secret=client_secret,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )
        self.accounts = InvestecAccountsClient(self._http_client)
        self.payments = InvestecPaymentsClient(self._http_client)
        self.documents = InvestecDocumentsClient(self._http_client)

    def check_auth(self) -> None:
        self._http_client._ensure_token()
