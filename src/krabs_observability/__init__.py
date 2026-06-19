"""OpenTelemetry setup and instrumentation helpers for Mr Krabs."""

from krabs_observability.agent import AgentRun, ResponseClient, ToolRunner
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
    current_trace_log_attributes,
    get_meter,
    get_tracer,
    initialize_observability,
    record_request_metric,
    trace_operation,
)

__all__ = [
    "AgentRun",
    "AttributeName",
    "MetricName",
    "ObservabilitySettings",
    "ResponseClient",
    "SpanName",
    "Telemetry",
    "ToolRunner",
    "TurnContext",
    "create_turn_context",
    "create_turn_context_from_env",
    "current_trace_log_attributes",
    "current_turn_context",
    "fastapi_app",
    "get_meter",
    "get_tracer",
    "initialize_observability",
    "record_request_metric",
    "safe_attributes",
    "trace_operation",
    "use_turn_context",
]
