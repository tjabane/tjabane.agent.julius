from __future__ import annotations
import json
import os
from pathlib import Path
from openai import OpenAI
from krabs_agent.library.agent import Agent
from krabs_agent.tools import ALL_DEFINITIONS, dispatch
from krabs_agent.tools.deps import ToolDeps
from krabs_domain.models.agent import Message
from krabs_domain.repositories.agent import SessionRepository
_SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "system.md").read_text()
_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
_sessions: SessionRepository | None = None




def _get_sessions() -> SessionRepository:
    global _sessions
    if _sessions is None:
        _sessions = SessionRepository()
    return _sessions


def run(
    whatsapp_number: str,
    user_message: str,
    *,
    sessions: SessionRepository | None = None,
    tool_deps: ToolDeps | None = None,
) -> str:
    sessions = sessions or _get_sessions()
    session = sessions.get_or_create(whatsapp_number)
    session.messages.append(Message(role="user", content=user_message))

    agent = Agent(
        model=_MODEL,
        system_prompt=_SYSTEM_PROMPT,
        tools=ALL_DEFINITIONS,
        messages=session.messages,
    )

    return agent.send_message(user_message)


def run_scheduled(
    schedule_id: str,
    query: str,
    *,
    client: OpenAI | None = None,
    tool_deps: ToolDeps | None = None,
) -> str:
    client = client or _get_client()

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]

    while True:
        response = client.chat.completions.create(
            model=_MODEL,
            tools=ALL_DEFINITIONS,
            messages=messages,
        )

        choice = response.choices[0]
        if choice.finish_reason == "stop":
            return choice.message.content or ""

        if choice.finish_reason == "tool_calls":
            messages.append(choice.message)
            for tool_call in choice.message.tool_calls:
                inputs = json.loads(tool_call.function.arguments)
                if tool_call.function.name == "send_email":
                    inputs["schedule_id"] = schedule_id
                result = _call_tool(tool_call.function.name, inputs, tool_deps)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })


def _call_tool(name: str, inputs: dict, deps: ToolDeps | None = None) -> str:
    try:
        return dispatch(name, inputs, deps)
    except Exception as exc:
        return f"Error: {exc}"
