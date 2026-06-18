from __future__ import annotations

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from krabs_observability.telemetry import Telemetry

_httpx_instrumented = False


def fastapi_app(app: FastAPI, telemetry: Telemetry) -> None:
    if not telemetry.enabled:
        return

    FastAPIInstrumentor.instrument_app(app)
    _instrument_httpx_once()


def _instrument_httpx_once() -> None:
    global _httpx_instrumented
    if _httpx_instrumented:
        return
    HTTPXClientInstrumentor().instrument()
    _httpx_instrumented = True
