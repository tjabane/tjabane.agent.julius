from __future__ import annotations

import os
import time

import httpx
import pytest

pytestmark = pytest.mark.e2e


def _base_url() -> str:
    value = os.environ.get("E2E_BASE_URL")
    if not value:
        pytest.fail("E2E_BASE_URL is required for end-to-end tests")
    return value.rstrip("/")


def _get_with_retry(path: str, *, expected_status: int = 200, timeout_seconds: float = 120.0) -> httpx.Response:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    url = f"{_base_url()}{path}"

    while time.monotonic() < deadline:
        try:
            response = httpx.get(url, timeout=10.0)
            if response.status_code == expected_status:
                return response
            last_error = AssertionError(f"Expected {expected_status}, got {response.status_code}: {response.text}")
        except httpx.HTTPError as exc:
            last_error = exc

        time.sleep(5)

    pytest.fail(f"GET {url} did not return {expected_status} within {timeout_seconds}s: {last_error}")


def test_dev_ping_endpoint_is_live():
    response = _get_with_retry("/ping")

    body = response.json()
    assert body["status"] == "ok"
    assert body["timestamp"]


def test_dev_legacy_ping_alias_is_live():
    response = _get_with_retry("/api/ping")

    assert response.json()["status"] == "ok"


def test_dev_health_endpoint_is_healthy():
    response = _get_with_retry("/health")

    body = response.json()
    assert body["status"] == "healthy"
    assert set(body["dependencies"]) >= {
        "cosmos_db",
        "investec_api",
        "investec_reachable",
        "openai",
        "twilio",
        "acs_email_config",
    }


def test_dev_webhook_rejects_invalid_payload():
    response = httpx.post(f"{_base_url()}/webhook", data={}, timeout=10.0)

    assert response.status_code == 400
