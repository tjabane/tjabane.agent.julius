from __future__ import annotations

import logging
import os
import time
from collections.abc import Iterator, Mapping, Set
from contextlib import contextmanager
from dataclasses import dataclass

from opentelemetry import metrics, trace
from opentelemetry.metrics import Counter, Histogram
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import ALWAYS_OFF, ALWAYS_ON, ParentBased, TraceIdRatioBased
from opentelemetry.trace import Span, Tracer

from krabs_observability.context import current_turn_context
from krabs_observability.semantic import AttributeName, MetricName, SpanName, safe_attributes

try:
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
except ImportError:  # pragma: no cover - dependency presence is verified by import tests.
    OTLPMetricExporter = None  # type: ignore[assignment]
    OTLPSpanExporter = None  # type: ignore[assignment]


_INSTRUMENTATION_NAME = "krabs"
_configured = False
_logger = logging.getLogger(__name__)
_counters: dict[str, Counter] = {}
_histograms: dict[str, Histogram] = {}
_SPAN_METRICS = {
    SpanName.WEBHOOK_PARSE: (MetricName.REQUEST_COUNT, MetricName.REQUEST_DURATION),
    SpanName.AGENT_RUN: (MetricName.AGENT_RUN_COUNT, MetricName.AGENT_RUN_DURATION),
    SpanName.MODEL_CALL: (MetricName.MODEL_CALL_COUNT, MetricName.MODEL_CALL_DURATION),
    SpanName.TOOL_CALL: (MetricName.TOOL_CALL_COUNT, MetricName.TOOL_CALL_DURATION),
    SpanName.INVESTEC_OPERATION: (
        MetricName.DEPENDENCY_OPERATION_COUNT,
        MetricName.DEPENDENCY_OPERATION_DURATION,
    ),
    SpanName.TWILIO_SEND: (
        MetricName.DEPENDENCY_OPERATION_COUNT,
        MetricName.DEPENDENCY_OPERATION_DURATION,
    ),
    SpanName.SESSION_LOAD: (
        MetricName.DEPENDENCY_OPERATION_COUNT,
        MetricName.DEPENDENCY_OPERATION_DURATION,
    ),
    SpanName.SESSION_SAVE: (
        MetricName.DEPENDENCY_OPERATION_COUNT,
        MetricName.DEPENDENCY_OPERATION_DURATION,
    ),
}


@dataclass(frozen=True)
class ObservabilitySettings:
    mode: str = "disabled"
    service_name: str = "mr-krabs"
    environment: str = "local"
    resource_attributes: str = ""
    traces_sampler: str = "parentbased_traceidratio"
    traces_sampler_arg: str = "1.0"

    @classmethod
    def from_env(cls) -> ObservabilitySettings:
        return cls(
            mode=os.environ.get("OTEL_MODE", "disabled"),
            service_name=os.environ.get("OTEL_SERVICE_NAME", "mr-krabs"),
            environment=os.environ.get("OTEL_ENVIRONMENT", os.environ.get("APP_ENV", "local")),
            resource_attributes=os.environ.get("OTEL_RESOURCE_ATTRIBUTES", ""),
            traces_sampler=os.environ.get("OTEL_TRACES_SAMPLER", "parentbased_traceidratio"),
            traces_sampler_arg=os.environ.get("OTEL_TRACES_SAMPLER_ARG", "1.0"),
        )

    @property
    def normalized_mode(self) -> str:
        return self.mode.strip().lower()

    @property
    def enabled(self) -> bool:
        return self.normalized_mode in {"console", "otlp"}


@dataclass(frozen=True)
class Telemetry:
    enabled: bool
    tracer: Tracer
    meter: metrics.Meter


def initialize_observability(settings: ObservabilitySettings | None = None) -> Telemetry:
    settings = settings or ObservabilitySettings.from_env()
    if settings.enabled:
        _configure_providers_once(settings)
    return Telemetry(
        enabled=settings.enabled,
        tracer=get_tracer(),
        meter=get_meter(),
    )


def get_tracer() -> Tracer:
    return trace.get_tracer(_INSTRUMENTATION_NAME)


def get_meter() -> metrics.Meter:
    return metrics.get_meter(_INSTRUMENTATION_NAME)


def current_trace_log_attributes() -> dict[str, str]:
    span_context = trace.get_current_span().get_span_context()
    if not span_context.is_valid:
        return {}
    return {
        "trace_id": trace.format_trace_id(span_context.trace_id),
        "span_id": trace.format_span_id(span_context.span_id),
    }


@contextmanager
def trace_operation(
    span_name: str,
    *,
    attributes: Mapping[str, object] | None = None,
    allowed_attribute_names: Set[str] | None = None,
    emit_metrics: bool = True,
) -> Iterator[Span]:
    allowed_names = set(allowed_attribute_names or set())
    allowed_names.update(
        {
            AttributeName.ERROR_TYPE,
            AttributeName.SESSION_ID,
            AttributeName.STATUS,
            AttributeName.TURN_ID,
        }
    )
    span_attributes: dict[str, object] = dict(attributes or {})
    if turn_context := current_turn_context():
        span_attributes.setdefault(AttributeName.TURN_ID, turn_context.turn_id)
        span_attributes.setdefault(AttributeName.SESSION_ID, turn_context.session_id)
    sanitized_attributes = safe_attributes(span_attributes, allowed_names=allowed_names)
    metric_allowed_names = _metric_attribute_names(span_name, allowed_names)
    metric_attributes = safe_attributes(span_attributes, allowed_names=metric_allowed_names)
    started_at = time.perf_counter()

    with get_tracer().start_as_current_span(
        span_name,
        attributes=sanitized_attributes,
    ) as span:
        try:
            yield span
            span.set_attribute(AttributeName.STATUS, "success")
            if emit_metrics:
                _record_operation_metrics(
                    span_name,
                    elapsed_seconds=time.perf_counter() - started_at,
                    status="success",
                    attributes=metric_attributes,
                )
        except Exception as exc:
            span.set_attribute(AttributeName.STATUS, "error")
            span.set_attribute(AttributeName.ERROR_TYPE, type(exc).__name__)
            span.record_exception(exc)
            error_type = type(exc).__name__
            if emit_metrics:
                _record_operation_metrics(
                    span_name,
                    elapsed_seconds=time.perf_counter() - started_at,
                    status="error",
                    attributes=metric_attributes,
                    error_type=error_type,
                )
            _logger.error(
                "Observed operation failed: %s",
                span_name,
                extra={**current_trace_log_attributes(), AttributeName.ERROR_TYPE: error_type},
            )
            raise


def record_request_metric(
    *,
    route: str,
    status: str,
    elapsed_seconds: float,
    http_status_code: int | None = None,
) -> None:
    attributes: dict[str, object] = {AttributeName.OPERATION_NAME: route}
    if http_status_code is not None:
        attributes[AttributeName.HTTP_STATUS_CODE] = http_status_code
    _record_operation_metrics(
        SpanName.WEBHOOK_PARSE,
        elapsed_seconds=elapsed_seconds,
        status=status,
        attributes=safe_attributes(
            attributes,
            allowed_names={AttributeName.OPERATION_NAME, AttributeName.HTTP_STATUS_CODE},
        ),
    )


def _record_operation_metrics(
    span_name: str,
    *,
    elapsed_seconds: float,
    status: str,
    attributes: Mapping[str, object],
    error_type: str | None = None,
) -> None:
    metric_names = _SPAN_METRICS.get(span_name)
    if metric_names is None:
        return

    count_name, duration_name = metric_names
    metric_attrs: dict[str, object] = dict(attributes)
    metric_attrs[AttributeName.STATUS] = status
    if error_type:
        metric_attrs[AttributeName.ERROR_TYPE] = error_type
    safe_metric_attrs = safe_attributes(
        metric_attrs,
        allowed_names=_metric_attribute_names(span_name, set(metric_attrs)),
    )
    _counter(count_name).add(1, attributes=safe_metric_attrs)
    _histogram(duration_name).record(elapsed_seconds, attributes=safe_metric_attrs)


def _metric_attribute_names(span_name: str, allowed_names: Set[str]) -> set[str]:
    names = {
        AttributeName.AGENT_MODEL,
        AttributeName.DEPENDENCY_NAME,
        AttributeName.ERROR_TYPE,
        AttributeName.HTTP_STATUS_CODE,
        AttributeName.MESSAGING_PROVIDER,
        AttributeName.OPERATION_NAME,
        AttributeName.STATUS,
        AttributeName.TOOL_NAME,
    }
    if span_name == SpanName.WEBHOOK_PARSE:
        names.add(AttributeName.MESSAGING_PROVIDER)
    return names.intersection(allowed_names | names)


def _counter(name: str) -> Counter:
    if name not in _counters:
        _counters[name] = get_meter().create_counter(name)
    return _counters[name]


def _histogram(name: str) -> Histogram:
    if name not in _histograms:
        _histograms[name] = get_meter().create_histogram(name, unit="s")
    return _histograms[name]


def _configure_providers_once(settings: ObservabilitySettings) -> None:
    global _configured
    if _configured:
        return

    resource = _resource_from_settings(settings)
    trace_provider = TracerProvider(resource=resource, sampler=_sampler_from_settings(settings))
    trace_provider.add_span_processor(BatchSpanProcessor(_span_exporter(settings)))
    trace.set_tracer_provider(trace_provider)

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[PeriodicExportingMetricReader(_metric_exporter(settings))],
    )
    metrics.set_meter_provider(meter_provider)
    _configured = True


def _resource_from_settings(settings: ObservabilitySettings) -> Resource:
    attributes: dict[str, str] = {
        "service.name": settings.service_name,
        "deployment.environment": settings.environment,
    }
    attributes.update(_parse_resource_attributes(settings.resource_attributes))
    return Resource.create(attributes)


def _parse_resource_attributes(raw_attributes: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in raw_attributes.split(","):
        if "=" not in item:
            continue
        name, value = item.split("=", 1)
        name = name.strip()
        value = value.strip()
        if name and value:
            parsed[name] = value
    return parsed


def _sampler_from_settings(settings: ObservabilitySettings):
    sampler_name = settings.traces_sampler.strip().lower()
    if sampler_name == "always_on":
        return ALWAYS_ON
    if sampler_name == "always_off":
        return ALWAYS_OFF
    if sampler_name == "traceidratio":
        return TraceIdRatioBased(_sampling_ratio(settings.traces_sampler_arg))
    if sampler_name == "parentbased_traceidratio":
        return ParentBased(TraceIdRatioBased(_sampling_ratio(settings.traces_sampler_arg)))
    return ParentBased(TraceIdRatioBased(1.0))


def _sampling_ratio(raw_ratio: str) -> float:
    try:
        ratio = float(raw_ratio)
    except ValueError:
        return 1.0
    return min(max(ratio, 0.0), 1.0)


def _span_exporter(settings: ObservabilitySettings):
    if settings.normalized_mode == "otlp":
        if OTLPSpanExporter is None:
            raise RuntimeError("OTLP span exporter is not installed.")
        return OTLPSpanExporter()
    return ConsoleSpanExporter()


def _metric_exporter(settings: ObservabilitySettings):
    if settings.normalized_mode == "otlp":
        if OTLPMetricExporter is None:
            raise RuntimeError("OTLP metric exporter is not installed.")
        return OTLPMetricExporter()
    return ConsoleMetricExporter()
