from __future__ import annotations

import asyncio
import json
from typing import Any, cast

from openai import OpenAI

from krabs_domain.models.agent import Message
from krabs_tools.registry import ToolRegistry


def _message_to_dict(message: Message) -> dict[str, str]:
    return {"role": message.role, "content": message.content}


def _function_calls(response: Any) -> list[Any]:
    return [item for item in response.output if getattr(item, "type", None) == "function_call"]


def _serialize_tool_output(output: Any) -> str:
    if isinstance(output, str):
        return output
    return json.dumps(output, default=str)


def _run_async_tool(coro: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    raise RuntimeError("Agent.send_message cannot execute async tools while an event loop is already running.")


class Agent:
    def __init__(
        self,
        model: str,
        system_prompt: str,
        messages: list[Message] | None = None,
        *,
        client: OpenAI,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.model = model
        self.messages: list[Any] = [{"role": "system", "content": system_prompt}]
        self.messages.extend(_message_to_dict(message) for message in messages or [])
        self._client = client
        self._tool_registry = tool_registry

    def send_message(self, message: str) -> str:
        input_list = [*self.messages, {"role": "user", "content": message}]
        tools = self._tool_registry.get_model_tools() if self._tool_registry else None
        request: dict[str, Any] = {"model": self.model, "input": input_list}
        if tools:
            request["tools"] = tools

        response = self._client.responses.create(**request)

        while self._tool_registry and (tool_calls := _function_calls(response)):
            tool_outputs = []
            for tool_call in tool_calls:
                tool = self._tool_registry.get(tool_call.name)
                tool_input = tool.input_schema.model_validate_json(tool_call.arguments or "{}")
                output = _run_async_tool(tool.run(tool_input))
                tool_outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": _serialize_tool_output(output),
                    }
                )

            response = self._client.responses.create(
                model=self.model,
                input=tool_outputs,
                previous_response_id=response.id,
                tools=cast(Any, tools),
            )

        reply = response.output_text or ""
        self.messages.append({"role": "user", "content": message})
        self.messages.append({"role": "assistant", "content": reply})
        return reply
