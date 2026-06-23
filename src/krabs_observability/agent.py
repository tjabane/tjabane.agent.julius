from __future__ import annotations

from typing import Any

from krabs_observability.semantic import AttributeName, SpanName
from krabs_observability.telemetry import trace_operation

_MODEL_CALL_ATTRS = {AttributeName.AGENT_MODEL, AttributeName.OPERATION_NAME}
_TOOL_CALL_ATTRS = {AttributeName.RESULT_COUNT, AttributeName.RESULT_KIND, AttributeName.TOOL_NAME}
_AGENT_RUN_ATTRS = {AttributeName.AGENT_MODEL}


class AgentRun:
    def __init__(self, *, model: str) -> None:
        self._model = model

    def run(self, call):
        with trace_operation(
            SpanName.AGENT_RUN,
            attributes={AttributeName.AGENT_MODEL: self._model},
            allowed_attribute_names=_AGENT_RUN_ATTRS,
        ):
            return call()


class ResponseClient:
    def __init__(self, inner: Any, *, model: str) -> None:
        self._inner = inner
        self._model = model

    def create(self, **request: Any) -> Any:
        with trace_operation(
            SpanName.MODEL_CALL,
            attributes={
                AttributeName.AGENT_MODEL: self._model,
                AttributeName.OPERATION_NAME: "responses.create",
            },
            allowed_attribute_names=_MODEL_CALL_ATTRS,
        ):
            return self._inner.responses.create(**request)


class ToolRunner:
    async def run(self, tool: Any, input_data: Any) -> Any:
        with trace_operation(
            SpanName.TOOL_CALL,
            attributes={AttributeName.TOOL_NAME: tool.name},
            allowed_attribute_names=_TOOL_CALL_ATTRS,
        ) as span:
            output = await tool.run(input_data)
            for name, value in result_attributes(output).items():
                span.set_attribute(name, value)
            return output


def result_attributes(output: Any) -> dict[str, str | int]:
    if isinstance(output, list):
        return {
            AttributeName.RESULT_KIND: "list",
            AttributeName.RESULT_COUNT: len(output),
        }
    if isinstance(output, dict):
        return {AttributeName.RESULT_KIND: "object"}
    if output is None:
        return {AttributeName.RESULT_KIND: "none"}
    return {AttributeName.RESULT_KIND: type(output).__name__}
