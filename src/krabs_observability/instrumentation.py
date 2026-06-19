from __future__ import annotations

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

from krabs_observability.telemetry import Telemetry

_httpx_instrumented = False
_logging_instrumented = False


def fastapi_app(app: FastAPI, telemetry: Telemetry) -> None:
    if not telemetry.enabled:
        return

    FastAPIInstrumentor.instrument_app(app)
    _instrument_httpx_once()
    _instrument_logging_once()


def _instrument_httpx_once() -> None:
    global _httpx_instrumented
    if _httpx_instrumented:
        return
    HTTPXClientInstrumentor().instrument()
    _httpx_instrumented = True


def _instrument_logging_once() -> None:
    global _logging_instrumented
    if _logging_instrumented:
        return
    LoggingInstrumentor().instrument(set_logging_format=False)
    _logging_instrumented = True
