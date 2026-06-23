from fastapi import FastAPI

from krabs_observability.instrumentation import fastapi_app
from krabs_observability.telemetry import Telemetry, get_meter, get_tracer


def test_fastapi_instrumentation_is_skipped_when_observability_is_disabled(monkeypatch) -> None:
    calls = []

    monkeypatch.setattr(
        "krabs_observability.instrumentation.FastAPIInstrumentor.instrument_app",
        lambda app: calls.append(app),
    )

    app = FastAPI()
    fastapi_app(app, Telemetry(enabled=False, tracer=get_tracer(), meter=get_meter()))

    assert calls == []


def test_fastapi_instrumentation_runs_when_observability_is_enabled(monkeypatch) -> None:
    calls = []

    monkeypatch.setattr(
        "krabs_observability.instrumentation.FastAPIInstrumentor.instrument_app",
        lambda app: calls.append(("fastapi", app)),
    )
    monkeypatch.setattr(
        "krabs_observability.instrumentation.HTTPXClientInstrumentor.instrument",
        lambda self: calls.append(("httpx", None)),
    )
    monkeypatch.setattr(
        "krabs_observability.instrumentation.LoggingInstrumentor.instrument",
        lambda self, **kwargs: calls.append(("logging", kwargs)),
    )
    monkeypatch.setattr("krabs_observability.instrumentation._httpx_instrumented", False)
    monkeypatch.setattr("krabs_observability.instrumentation._logging_instrumented", False)

    app = FastAPI()
    fastapi_app(app, Telemetry(enabled=True, tracer=get_tracer(), meter=get_meter()))

    assert calls == [
        ("fastapi", app),
        ("httpx", None),
        ("logging", {"set_logging_format": False}),
    ]
