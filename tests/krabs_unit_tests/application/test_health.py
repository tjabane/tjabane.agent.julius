from unittest.mock import MagicMock, patch

import httpx
import pytest

from krabs_application import health


def test_timed_returns_healthy_result_for_successful_check():
    result = health._timed(health.HealthCheck("ok", lambda: None)).as_dict()

    assert result["status"] == "healthy"
    assert "latency_ms" in result
    assert "error" not in result


def test_timed_sanitizes_unhealthy_error_details():
    def failing_check() -> None:
        raise RuntimeError("secret endpoint detail")

    result = health._timed(health.HealthCheck("failing", failing_check)).as_dict()

    assert result["status"] == "unhealthy"
    assert result["error"] == "RuntimeError"
    assert "secret endpoint detail" not in str(result)


def test_run_all_aggregates_healthy_checks(monkeypatch):
    checks = (
        health.HealthCheck("first", lambda: None),
        health.HealthCheck("second", lambda: None),
    )
    monkeypatch.setattr(health, "CHECKS", checks)

    result = health.run_all()

    assert result["status"] == "healthy"
    assert result["dependencies"]["first"]["status"] == "healthy"
    assert result["dependencies"]["second"]["status"] == "healthy"


def test_run_all_marks_unhealthy_when_critical_check_fails(monkeypatch):
    def failing_check() -> None:
        raise RuntimeError("boom")

    checks = (
        health.HealthCheck("optional", failing_check, critical=False),
        health.HealthCheck("critical", failing_check),
    )
    monkeypatch.setattr(health, "CHECKS", checks)

    result = health.run_all()

    assert result["status"] == "unhealthy"
    assert result["dependencies"]["optional"]["status"] == "unhealthy"
    assert result["dependencies"]["critical"]["status"] == "unhealthy"


def test_run_all_ignores_noncritical_failure_for_overall_status(monkeypatch):
    def failing_check() -> None:
        raise RuntimeError("boom")

    checks = (
        health.HealthCheck("optional", failing_check, critical=False),
        health.HealthCheck("critical", lambda: None),
    )
    monkeypatch.setattr(health, "CHECKS", checks)

    result = health.run_all()

    assert result["status"] == "healthy"
    assert result["dependencies"]["optional"]["status"] == "unhealthy"


@patch("krabs_application.health.httpx.get")
def test_investec_reachable_allows_client_error_status(mock_get):
    request = httpx.Request("GET", "https://openapisandbox.investec.com")
    response = httpx.Response(404, request=request)
    mock_get.return_value = response

    health._check_investec_reachable()


@patch("krabs_application.health.httpx.get")
def test_investec_reachable_raises_on_server_error_status(mock_get):
    response = MagicMock()
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500",
        request=MagicMock(),
        response=MagicMock(status_code=500),
    )
    mock_get.return_value = response

    with pytest.raises(httpx.HTTPStatusError):
        health._check_investec_reachable()

    response.raise_for_status.assert_called_once()


@patch("krabs_application.health.InvestecClient")
def test_investec_check_uses_public_auth_check(mock_client_cls):
    client = MagicMock()
    mock_client_cls.return_value = client

    health._check_investec()

    mock_client_cls.assert_called_once_with(timeout=health._TIMEOUT_SECONDS)
    client.check_auth.assert_called_once_with()
