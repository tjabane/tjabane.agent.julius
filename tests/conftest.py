import os
import pytest


@pytest.fixture(autouse=True)
def investec_env(monkeypatch):
    """Provide dummy env vars so InvestecClient can be instantiated in unit tests."""
    monkeypatch.setenv("INVESTEC_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("INVESTEC_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("INVESTEC_API_KEY", "test-api-key")
    monkeypatch.setenv("INVESTEC_SANDBOX", "true")
