from __future__ import annotations

import os
from dataclasses import dataclass

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import ALWAYS_OFF, ALWAYS_ON, ParentBased, TraceIdRatioBased
from opentelemetry.trace import Tracer

try:
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
except ImportError:  # pragma: no cover - dependency presence is verified by import tests.
    OTLPMetricExporter = None  # type: ignore[assignment]
    OTLPSpanExporter = None  # type: ignore[assignment]


_INSTRUMENTATION_NAME = "krabs"
_configured = False


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
