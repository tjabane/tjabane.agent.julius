from __future__ import annotations
import json
import os
from pathlib import Path
from openai import OpenAI
from julius_domain.models.agent import Message
from julius_domain.repositories.agent import SessionRepository
from julius_application.agent.tools import ALL_DEFINITIONS, dispatch
from julius_application.agent.tools.deps import ToolDeps
from julius_application.observability import (
    hash_identifier,
    mark_success,
    record_exception,
    set_attributes,
    start_span,
)

_SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "system.md").read_text()
_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

_client: OpenAI | None = None
_sessions: SessionRepository | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def _get_sessions() -> SessionRepository:
    global _sessions
    if _sessions is None:
        _sessions = SessionRepository()
    return _sessions


def run(
    whatsapp_number: str,
    user_message: str,
    *,
    client: OpenAI | None = None,
    sessions: SessionRepository | None = None,
    tool_deps: ToolDeps | None = None,
) -> str:
    with start_span("agent.run", {
        "app.operation": "agent.run",
        "user.hash": hash_identifier(whatsapp_number),
        "gen_ai.system": "openai",
        "gen_ai.request.model": _MODEL,
    }) as span:
        client = client or _get_client()
        sessions = sessions or _get_sessions()

        session = sessions.get_or_create(whatsapp_number)
        session.messages.append(Message(role="user", content=user_message))

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            *[{"role": m.role, "content": m.content} for m in session.messages],
        ]

        while True:
            with start_span("openai.chat.completions", {
                "gen_ai.system": "openai",
                "gen_ai.request.model": _MODEL,
            }) as openai_span:
                response = client.chat.completions.create(
                    model=_MODEL,
                    tools=ALL_DEFINITIONS,
                    messages=messages,
                )
                mark_success(openai_span)

            choice = response.choices[0]
            set_attributes(span, {"gen_ai.response.finish_reason": choice.finish_reason})

            if choice.finish_reason == "stop":
                reply = choice.message.content or ""
                session.messages.append(Message(role="assistant", content=reply))
                sessions.save(session)
                mark_success(span)
                return reply

            if choice.finish_reason == "tool_calls":
                messages.append(choice.message)
                for tool_call in choice.message.tool_calls:
                    inputs = json.loads(tool_call.function.arguments)
                    result = _call_tool(tool_call.function.name, inputs, tool_deps)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })


def run_scheduled(
    schedule_id: str,
    query: str,
    *,
    client: OpenAI | None = None,
    tool_deps: ToolDeps | None = None,
) -> str:
    with start_span("agent.run_scheduled", {
        "app.operation": "agent.run_scheduled",
        "app.schedule_id": schedule_id,
        "gen_ai.system": "openai",
        "gen_ai.request.model": _MODEL,
    }) as span:
        client = client or _get_client()

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ]

        while True:
            with start_span("openai.chat.completions", {
                "gen_ai.system": "openai",
                "gen_ai.request.model": _MODEL,
            }) as openai_span:
                response = client.chat.completions.create(
                    model=_MODEL,
                    tools=ALL_DEFINITIONS,
                    messages=messages,
                )
                mark_success(openai_span)

            choice = response.choices[0]
            set_attributes(span, {"gen_ai.response.finish_reason": choice.finish_reason})

            if choice.finish_reason == "stop":
                mark_success(span)
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
    with start_span("agent.tool_call", {"tool.name": name}) as span:
        try:
            result = dispatch(name, inputs, deps)
            mark_success(span)
            return result
        except Exception as e:
            record_exception(span, e)
            return f"Error: {e}"
