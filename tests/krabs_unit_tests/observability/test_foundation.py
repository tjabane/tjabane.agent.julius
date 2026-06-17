from krabs_observability.context import create_turn_context
from krabs_observability.semantic import AttributeName, SpanName, safe_attributes
from krabs_observability.telemetry import ObservabilitySettings, initialize_observability


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
