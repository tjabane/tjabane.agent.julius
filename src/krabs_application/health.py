from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Literal

import httpx
from azure.communication.email import EmailClient
from azure.cosmos import CosmosClient
from openai import OpenAI
from twilio.rest import Client as TwilioRestClient

from krabs_services.communication.providers import (
    get_message_sender,
    get_report_sender,
    use_in_memory_communication,
)
from krabs_services.finance.investec_client import InvestecClient, get_investec_base_url

_TIMEOUT_SECONDS = 5.0

HealthStatus = Literal["healthy", "unhealthy"]
Check = Callable[[], None]


@dataclass(frozen=True)
class HealthCheck:
    name: str
    check: Check
    critical: bool = True


@dataclass(frozen=True)
class HealthResult:
    status: HealthStatus
    latency_ms: float
    error: str | None = None

    def as_dict(self) -> dict:
        result: dict[str, str | float] = {
            "status": self.status,
            "latency_ms": self.latency_ms,
        }
        if self.error:
            result["error"] = self.error
        return result


def _timed(health_check: HealthCheck) -> HealthResult:
    start = time.perf_counter()
    try:
        health_check.check()
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        return HealthResult(status="healthy", latency_ms=latency_ms)
    except Exception as exc:
        logging.exception("Health check failed: %s", health_check.name)
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        return HealthResult(
            status="unhealthy",
            latency_ms=latency_ms,
            error=type(exc).__name__,
        )


def _check_cosmos() -> None:
    client = CosmosClient.from_connection_string(os.environ["COSMOS_CONNECTION_STRING"])
    database = client.get_database_client(os.environ["COSMOS_DATABASE"])
    database.read()


def _check_investec() -> None:
    InvestecClient(timeout=_TIMEOUT_SECONDS).check_auth()


def _check_openai() -> None:
    client = OpenAI(timeout=_TIMEOUT_SECONDS)
    next(iter(client.models.list()), None)


def _check_twilio() -> None:
    if use_in_memory_communication():
        get_message_sender()
        return

    client = TwilioRestClient(
        os.environ["TWILIO_ACCOUNT_SID"],
        os.environ["TWILIO_AUTH_TOKEN"],
    )
    client.api.accounts(os.environ["TWILIO_ACCOUNT_SID"]).fetch()


def _check_acs_email_config() -> None:
    if use_in_memory_communication():
        get_report_sender()
        return

    EmailClient.from_connection_string(os.environ["AZURE_COMMUNICATION_CONNECTION_STRING"])
    if not os.environ.get("EMAIL_SENDER_ADDRESS"):
        raise RuntimeError("EMAIL_SENDER_ADDRESS is not set")


def _check_investec_reachable() -> None:
    base = (os.environ.get("INVESTEC_BASE_URL") or get_investec_base_url()).rstrip("/")
    response = httpx.get(base, timeout=_TIMEOUT_SECONDS)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if 400 <= exc.response.status_code < 500:
            return
        raise


CHECKS: tuple[HealthCheck, ...] = (
    HealthCheck("cosmos_db", _check_cosmos),
    HealthCheck("investec_api", _check_investec),
    HealthCheck("investec_reachable", _check_investec_reachable),
    HealthCheck("openai", _check_openai),
    HealthCheck("twilio", _check_twilio),
    HealthCheck("acs_email_config", _check_acs_email_config),
)


def run_all() -> dict:
    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=len(CHECKS)) as pool:
        future_to_check = {pool.submit(_timed, health_check): health_check for health_check in CHECKS}
        for future in as_completed(future_to_check):
            health_check = future_to_check[future]
            results[health_check.name] = future.result().as_dict()

    critical_results = [
        results[health_check.name]
        for health_check in CHECKS
        if health_check.critical
    ]
    overall = "healthy" if all(r["status"] == "healthy" for r in critical_results) else "unhealthy"
    return {"status": overall, "dependencies": results}
