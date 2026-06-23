from krabs_observability.context import create_turn_context
from krabs_observability.semantic import FORBIDDEN_ATTRIBUTE_NAMES, AttributeName, SpanName, safe_attributes
from krabs_observability.telemetry import (
    ObservabilitySettings,
    initialize_observability,
    trace_operation,
)


class FakeMetricInstrument:
    def __init__(self) -> None:
        self.records: list[tuple[float, dict[str, object]]] = []

    def add(self, value: float, *, attributes: dict[str, object]) -> None:
        self.records.append((value, dict(attributes)))

    def record(self, value: float, *, attributes: dict[str, object]) -> None:
        self.records.append((value, dict(attributes)))


class FakeMeter:
    def __init__(self) -> None:
        self.counters: dict[str, FakeMetricInstrument] = {}
        self.histograms: dict[str, FakeMetricInstrument] = {}

    def create_counter(self, name: str) -> FakeMetricInstrument:
        self.counters[name] = FakeMetricInstrument()
        return self.counters[name]

    def create_histogram(self, name: str, *, unit: str) -> FakeMetricInstrument:
        assert unit == "s"
        self.histograms[name] = FakeMetricInstrument()
        return self.histograms[name]


def test_disabled_observability_returns_noop_safe_accessors() -> None:
    telemetry = initialize_observability(ObservabilitySettings(mode="disabled"))

    assert not telemetry.enabled
    assert telemetry.tracer is not None
    assert telemetry.meter is not None


def test_safe_attributes_only_allows_approved_non_sensitive_values() -> None:
    attrs = safe_attributes(
        {
            AttributeName.TURN_ID: "turn-1",
            AttributeName.TOOL_NAME: "get_accounts",
            "phone.number": "+27821234567",
            "message.body": "what is my balance?",
            "raw.tool.output": {"balance": "1000.00"},
        },
        allowed_names={AttributeName.TURN_ID, AttributeName.TOOL_NAME},
    )

    assert attrs == {
        AttributeName.TURN_ID: "turn-1",
        AttributeName.TOOL_NAME: "get_accounts",
    }


def test_safe_attributes_rejects_forbidden_names_even_when_allowed() -> None:
    attrs = safe_attributes(
        {"message.body": "private text"},
        allowed_names={"message.body"},
    )

    assert attrs == {}


def test_forbidden_sensitive_fields_never_pass_safe_attributes() -> None:
    attrs = safe_attributes(
        {name: f"private-{name}" for name in FORBIDDEN_ATTRIBUTE_NAMES},
        allowed_names=set(FORBIDDEN_ATTRIBUTE_NAMES),
    )

    assert attrs == {}


def test_turn_context_uses_stable_private_session_id() -> None:
    first = create_turn_context(
        "whatsapp:+27821234567",
        secret="test-secret",
        turn_id="turn-1",
    )
    second = create_turn_context(
        "+27821234567",
        secret="test-secret",
        turn_id="turn-2",
    )

    assert first.turn_id == "turn-1"
    assert second.turn_id == "turn-2"
    assert first.session_id == second.session_id
    assert "+27821234567" not in first.session_id
    assert first.session_id.startswith("wa_")


def test_semantic_names_are_stable() -> None:
    assert SpanName.AGENT_RUN == "agent.run"
    assert SpanName.TOOL_CALL == "tool.call"


def test_trace_operation_records_bounded_red_metrics_without_sensitive_attributes(monkeypatch) -> None:
    meter = FakeMeter()
    monkeypatch.setattr("krabs_observability.telemetry.get_meter", lambda: meter)
    monkeypatch.setattr("krabs_observability.telemetry._counters", {})
    monkeypatch.setattr("krabs_observability.telemetry._histograms", {})

    with trace_operation(
        SpanName.TOOL_CALL,
        attributes={
            AttributeName.TOOL_NAME: "get_balance",
            AttributeName.TURN_ID: "turn-1",
            AttributeName.SESSION_ID: "wa_safe",
            "phone.number": "+27821234567",
            "message.body": "show my private balance",
            "investec.payload": {"accountId": "private-account-id"},
        },
        allowed_attribute_names={
            AttributeName.SESSION_ID,
            AttributeName.TOOL_NAME,
            AttributeName.TURN_ID,
            "phone.number",
            "message.body",
            "investec.payload",
        },
    ):
        pass

    counter_attrs = meter.counters["krabs.tool.call.count"].records[0][1]
    histogram_attrs = meter.histograms["krabs.tool.call.duration"].records[0][1]

    assert counter_attrs == {"status": "success", "tool.name": "get_balance"}
    assert histogram_attrs == counter_attrs
    emitted = f"{counter_attrs} {histogram_attrs}"
    assert "+27821234567" not in emitted
    assert "show my private balance" not in emitted
    assert "private-account-id" not in emitted


def test_trace_operation_error_log_uses_trace_metadata_without_payloads(monkeypatch, caplog) -> None:
    meter = FakeMeter()
    monkeypatch.setattr("krabs_observability.telemetry.get_meter", lambda: meter)
    monkeypatch.setattr("krabs_observability.telemetry._counters", {})
    monkeypatch.setattr("krabs_observability.telemetry._histograms", {})
    monkeypatch.setattr(
        "krabs_observability.telemetry.current_trace_log_attributes",
        lambda: {"trace_id": "trace-1", "span_id": "span-1"},
    )

    try:
        with trace_operation(
            SpanName.INVESTEC_OPERATION,
            attributes={
                AttributeName.DEPENDENCY_NAME: "investec",
                AttributeName.OPERATION_NAME: "balance.get",
                "account.number": "1234567890",
                "transaction.description": "private purchase",
            },
            allowed_attribute_names={
                AttributeName.DEPENDENCY_NAME,
                AttributeName.OPERATION_NAME,
                "account.number",
                "transaction.description",
            },
        ):
            raise RuntimeError("provider failed")
    except RuntimeError:
        pass

    assert caplog.records
    record = caplog.records[-1]
    assert record.trace_id == "trace-1"
    assert record.span_id == "span-1"
    assert "investec.operation" in record.getMessage()
    assert "1234567890" not in record.getMessage()
    assert "private purchase" not in record.getMessage()
