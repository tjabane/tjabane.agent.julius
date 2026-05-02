import os
import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(autouse=True)
def investec_env(monkeypatch, request):
    """Provide dummy env vars for unit tests. Integration tests use real .env values."""
    if request.node.get_closest_marker("integration"):
        return
    monkeypatch.setenv("INVESTEC_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("INVESTEC_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("INVESTEC_API_KEY", "test-api-key")
    monkeypatch.setenv("INVESTEC_SANDBOX", "true")
