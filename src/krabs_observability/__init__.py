"""OpenTelemetry setup and instrumentation helpers for Mr Krabs."""

from krabs_observability.context import TurnContext, create_turn_context
from krabs_observability.semantic import AttributeName, MetricName, SpanName, safe_attributes
from krabs_observability.telemetry import (
    ObservabilitySettings,
    Telemetry,
    get_meter,
    get_tracer,
    initialize_observability,
)

__all__ = [
    "AttributeName",
    "MetricName",
    "ObservabilitySettings",
    "SpanName",
    "Telemetry",
    "TurnContext",
    "create_turn_context",
    "get_meter",
    "get_tracer",
    "initialize_observability",
    "safe_attributes",
]
