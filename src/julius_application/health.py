from __future__ import annotations
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

import httpx
from azure.communication.email import EmailClient
from azure.cosmos import CosmosClient
from openai import OpenAI
from twilio.rest import Client as TwilioRestClient

from julius_services.finance.investec_client import InvestecClient


_TIMEOUT_SECONDS = 5.0


def _timed(check: Callable[[], None]) -> dict:
    start = time.perf_counter()
    try:
        check()
        return {"status": "healthy", "latency_ms": round((time.perf_counter() - start) * 1000, 1)}
    except Exception as e:
        return {
            "status": "unhealthy",
            "latency_ms": round((time.perf_counter() - start) * 1000, 1),
            "error": f"{type(e).__name__}: {e}",
        }


def _check_cosmos() -> None:
    client = CosmosClient.from_connection_string(os.environ["COSMOS_CONNECTION_STRING"])
    database = client.get_database_client(os.environ["COSMOS_DATABASE"])
    database.read()


def _check_investec() -> None:
    InvestecClient()._ensure_token()


def _check_openai() -> None:
    client = OpenAI(timeout=_TIMEOUT_SECONDS)
    next(iter(client.models.list()), None)


def _check_twilio() -> None:
    client = TwilioRestClient(
        os.environ["TWILIO_ACCOUNT_SID"],
        os.environ["TWILIO_AUTH_TOKEN"],
    )
    client.api.accounts(os.environ["TWILIO_ACCOUNT_SID"]).fetch()


def _check_acs_email() -> None:
    EmailClient.from_connection_string(os.environ["AZURE_COMMUNICATION_CONNECTION_STRING"])
    if not os.environ.get("EMAIL_SENDER_ADDRESS"):
        raise RuntimeError("EMAIL_SENDER_ADDRESS is not set")


def _check_investec_reachable() -> None:
    sandbox = os.environ.get("INVESTEC_SANDBOX", "true").lower() == "true"
    base = "https://openapisandbox.investec.com" if sandbox else "https://openapi.investec.com"
    httpx.get(base, timeout=_TIMEOUT_SECONDS)


CHECKS: dict[str, Callable[[], None]] = {
    "cosmos_db": _check_cosmos,
    "investec_api": _check_investec,
    "investec_reachable": _check_investec_reachable,
    "openai": _check_openai,
    "twilio": _check_twilio,
    "acs_email": _check_acs_email,
}


def run_all() -> dict:
    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=len(CHECKS)) as pool:
        future_to_name = {pool.submit(_timed, fn): name for name, fn in CHECKS.items()}
        for future in as_completed(future_to_name):
            results[future_to_name[future]] = future.result()

    overall = "healthy" if all(r["status"] == "healthy" for r in results.values()) else "unhealthy"
    return {"status": overall, "dependencies": results}
