from __future__ import annotations
import json
from collections.abc import Callable
from typing import Any
from openai import OpenAI
from krabs_agent.tools import dispatch
from krabs_agent.tools.deps import ToolDeps
from krabs_domain.models.agent import Message

_client: OpenAI | None = None
DispatchFn = Callable[[str, dict, ToolDeps | None], str]


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def _message_to_dict(message: Message) -> dict[str, str]:
    return {"role": message.role, "content": message.content}

class Agent:
    def __init__(
        self,
        model: str,
        system_prompt: str,
        tools: list[dict[str, Any]],
        messages: list[Message] | None = None,
        *,
        client: OpenAI | None = None,
        tool_deps: ToolDeps | None = None,
        dispatch_fn: DispatchFn = dispatch,
    ) -> None:
        self.model = model
        self.tools = tools
        self.messages: list[Any] = [{"role": "system", "content": system_prompt}]
        self.messages.extend(_message_to_dict(message) for message in messages or [])
        self._client = client or _get_client()
        self._tool_deps = tool_deps
        self._dispatch = dispatch_fn

    def send_message(self, message: str) -> str:
        input_list = [*self.messages, {"role": "user", "content": message}]
        while True:
            response = self._client.responses.create(
                    model=self.model,
                    input=input_list,
                    tools=self.tools,
                )
            input_list += response.output
            tool_calls = [ item for item in response.output if item.type == "function_call"]
            if not tool_calls:
                self.messages.append({"role": "assistant", "content": response.output_text})
                return response.output_text
            for item in tool_calls:
                tool_result = self._call_tool(item.name, item.arguments)
                self.messages.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": tool_result,
                })
                    
            

    def _call_tool(self, name: str, arguments: dict) -> str:
        try:
            result = self._dispatch(name, arguments, self._tool_deps)
        except Exception as exc:
            print(f"Error calling tool {name}: {exc}")
            result = f"Error: {exc}"
        return result
