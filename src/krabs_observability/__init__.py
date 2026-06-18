"""OpenTelemetry setup and instrumentation helpers for Mr Krabs."""

from krabs_observability.context import (
    TurnContext,
    create_turn_context,
    create_turn_context_from_env,
    current_turn_context,
    use_turn_context,
)
from krabs_observability.instrumentation import fastapi_app
from krabs_observability.semantic import AttributeName, MetricName, SpanName, safe_attributes
from krabs_observability.telemetry import (
    ObservabilitySettings,
    Telemetry,
    get_meter,
    get_tracer,
    initialize_observability,
    trace_operation,
)

__all__ = [
    "AttributeName",
    "MetricName",
    "ObservabilitySettings",
    "SpanName",
    "Telemetry",
    "TurnContext",
    "create_turn_context",
    "create_turn_context_from_env",
    "current_turn_context",
    "fastapi_app",
    "get_meter",
    "get_tracer",
    "initialize_observability",
    "safe_attributes",
    "trace_operation",
    "use_turn_context",
]
