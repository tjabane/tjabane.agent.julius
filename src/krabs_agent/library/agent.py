from __future__ import annotations
from typing import Any
from openai import OpenAI
from krabs_domain.models.agent import Message


def _message_to_dict(message: Message) -> dict[str, str]:
    return {"role": message.role, "content": message.content}

class Agent:
    def __init__(
        self,
        model: str,
        system_prompt: str,
        messages: list[Message] | None = None,
        *,
        client: OpenAI,
    ) -> None:
        self.model = model
        self.messages: list[Any] = [{"role": "system", "content": system_prompt}]
        self.messages.extend(_message_to_dict(message) for message in messages or [])
        self._client = client

    def send_message(self, message: str) -> str:
        input_list = [*self.messages, {"role": "user", "content": message}]

        response = self._client.responses.create(
            model=self.model,
            input=input_list,
        )

        reply = response.output_text or ""
        self.messages.append({"role": "user", "content": message})
        self.messages.append({"role": "assistant", "content": reply})
        return reply
