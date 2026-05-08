from __future__ import annotations

import hashlib
import logging
import os
from contextlib import contextmanager
from typing import Iterator

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Span, Status, StatusCode

_LOGGER = logging.getLogger(__name__)
_SERVICE_NAME = "julius"
_TRACER = trace.get_tracer(_SERVICE_NAME)
_CONFIGURED = False


def configure_observability() -> None:
    """Configure OpenTelemetry once, using Azure Monitor when configured."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if connection_string:
        try:
            configure_azure_monitor(
                connection_string=connection_string,
                resource=Resource.create({
                    "service.name": _SERVICE_NAME,
                    "deployment.environment": os.environ.get("APP_ENV", "local"),
                }),
            )
        except Exception:
            _LOGGER.exception("Failed to configure Azure Monitor OpenTelemetry")
    else:
        _LOGGER.info("APPLICATIONINSIGHTS_CONNECTION_STRING is not set; telemetry export disabled")

    _instrument_http_clients()
    _CONFIGURED = True


def get_tracer():
    return _TRACER


@contextmanager
def start_span(name: str, attributes: dict[str, object] | None = None) -> Iterator[Span]:
    with _TRACER.start_as_current_span(name) as span:
        set_attributes(span, {
            "service.name": _SERVICE_NAME,
            "deployment.environment": os.environ.get("APP_ENV", "local"),
            **(attributes or {}),
        })
        try:
            yield span
        except Exception as exc:
            record_exception(span, exc)
            raise


def set_attributes(span: Span, attributes: dict[str, object | None]) -> None:
    for key, value in attributes.items():
        if value is not None:
            span.set_attribute(key, value)


def mark_success(span: Span) -> None:
    span.set_status(Status(StatusCode.OK))
    span.set_attribute("app.status", "success")


def record_exception(span: Span, exc: Exception) -> None:
    span.record_exception(exc)
    span.set_status(Status(StatusCode.ERROR, type(exc).__name__))
    span.set_attribute("app.status", "failure")
    span.set_attribute("error.type", type(exc).__name__)


def hash_identifier(value: str | None) -> str | None:
    if not value:
        return None
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return digest[:16]


def _instrument_http_clients() -> None:
    try:
        HTTPXClientInstrumentor().instrument()
    except Exception:
        _LOGGER.exception("Failed to configure HTTP client OpenTelemetry instrumentation")
