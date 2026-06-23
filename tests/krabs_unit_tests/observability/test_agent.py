from __future__ import annotations

import asyncio
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

from pydantic import BaseModel

from krabs_observability.agent import AgentRun, ResponseClient, ToolRunner


def test_agent_run_wraps_agent_turn_in_safe_agent_run_span(monkeypatch) -> None:
    spans = []

    @contextmanager
    def fake_trace_operation(span_name, *, attributes, allowed_attribute_names):
        spans.append(
            {
                "span_name": span_name,
                "attributes": attributes,
                "allowed_attribute_names": allowed_attribute_names,
            }
        )
        yield

    monkeypatch.setattr("krabs_observability.agent.trace_operation", fake_trace_operation)

    assert AgentRun(model="test-model").run(lambda: "Done.") == "Done."

    assert spans == [
        {
            "span_name": "agent.run",
            "attributes": {"agent.model": "test-model"},
            "allowed_attribute_names": {"agent.model"},
        }
    ]


def test_response_client_wraps_model_calls_in_safe_model_spans(monkeypatch) -> None:
    spans = []
    client = MagicMock()
    client.responses.create.return_value = SimpleNamespace(output_text="Hi.")

    @contextmanager
    def fake_trace_operation(span_name, *, attributes, allowed_attribute_names):
        spans.append(
            {
                "span_name": span_name,
                "attributes": attributes,
                "allowed_attribute_names": allowed_attribute_names,
            }
        )
        yield

    monkeypatch.setattr("krabs_observability.agent.trace_operation", fake_trace_operation)
    response_client = ResponseClient(client, model="test-model")

    assert (
        response_client.create(model="test-model", input=[{"role": "user", "content": "private"}]).output_text == "Hi."
    )

    assert spans == [
        {
            "span_name": "openai.responses.create",
            "attributes": {
                "agent.model": "test-model",
                "operation.name": "responses.create",
            },
            "allowed_attribute_names": {"agent.model", "operation.name"},
        }
    ]


def test_tool_runner_wraps_tools_without_raw_arguments_or_outputs(monkeypatch) -> None:
    spans = []
    span_attributes = []

    class PrivateInput(BaseModel):
        private: str

    class PrivateTool:
        name = "private_tool"

        async def run(self, input_data: PrivateInput) -> list[dict[str, Any]]:
            return [{"accountId": "private-account-id", "accountName": "Cheque"}]

    class FakeSpan:
        def set_attribute(self, name, value):
            span_attributes.append((name, value))

    @contextmanager
    def fake_trace_operation(span_name, *, attributes, allowed_attribute_names):
        spans.append(
            {
                "span_name": span_name,
                "attributes": attributes,
                "allowed_attribute_names": allowed_attribute_names,
            }
        )
        yield FakeSpan()

    monkeypatch.setattr("krabs_observability.agent.trace_operation", fake_trace_operation)
    output = asyncio.run(ToolRunner().run(PrivateTool(), PrivateInput(private="value")))

    assert output == [{"accountId": "private-account-id", "accountName": "Cheque"}]
    assert spans == [
        {
            "span_name": "tool.call",
            "attributes": {"tool.name": "private_tool"},
            "allowed_attribute_names": {"result.count", "result.kind", "tool.name"},
        }
    ]
    assert ("result.kind", "list") in span_attributes
    assert ("result.count", 1) in span_attributes
    assert "value" not in str(spans)
    assert "Cheque" not in str(spans)
