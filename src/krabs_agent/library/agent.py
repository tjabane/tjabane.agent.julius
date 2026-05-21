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
        self.messages.append({"role": "user", "content": message})

        while True:
            response = self._client.chat.completions.create(
                model=self.model,
                tools=self.tools,
                messages=self.messages,
            )
            choice = response.choices[0]

            if choice.finish_reason == "stop":
                reply = choice.message.content or ""
                self.messages.append({"role": "assistant", "content": reply})
                return reply

            if choice.finish_reason == "tool_calls":
                self.messages.append(choice.message)
                for tool_call in choice.message.tool_calls:
                    inputs = json.loads(tool_call.function.arguments)
                    result = self._call_tool(tool_call.function.name, inputs)
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        }
                    )
                continue

            return choice.message.content or ""

    def _call_tool(self, name: str, inputs: dict) -> str:
        try:
            return self._dispatch(name, inputs, self._tool_deps)
        except Exception as exc:
            return f"Error: {exc}"
