from __future__ import annotations
import os
from pathlib import Path
from langfuse.openai import OpenAI
from krabs_agent.library.agent import Agent
from krabs_agent.observability import stable_trace_identifier
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
    client: OpenAI | None = None,
    sessions: SessionRepository | None = None,
    tool_deps: ToolDeps | None = None,
) -> str:
    sessions = sessions or _get_sessions()
    session = sessions.get_or_create(whatsapp_number)
    trace_user_id = stable_trace_identifier(whatsapp_number)

    agent = Agent(
        model=_MODEL,
        system_prompt=_SYSTEM_PROMPT,
        tools=ALL_DEFINITIONS,
        messages=session.messages,
        client=client,
        tool_deps=tool_deps,
        trace_name="whatsapp-agent-response",
        session_id=trace_user_id,
        user_id=trace_user_id,
        tags=["agent", "whatsapp"],
    )

    reply = agent.send_message(user_message)
    session.messages.append(Message(role="user", content=user_message))
    session.messages.append(Message(role="assistant", content=reply))
    sessions.save(session)
    return reply


def run_scheduled(
    schedule_id: str,
    query: str,
    *,
    client: OpenAI | None = None,
    tool_deps: ToolDeps | None = None,
) -> str:
    def dispatch_with_schedule_id(name: str, inputs: dict, deps: ToolDeps | None = None) -> str:
        if name == "send_email":
            inputs["schedule_id"] = schedule_id
        return dispatch(name, inputs, deps)

    agent = Agent(
        model=_MODEL,
        system_prompt=_SYSTEM_PROMPT,
        tools=ALL_DEFINITIONS,
        client=client,
        tool_deps=tool_deps,
        dispatch_fn=dispatch_with_schedule_id,
        trace_name="scheduled-agent-response",
        session_id=stable_trace_identifier(schedule_id),
        tags=["agent", "scheduled-report"],
    )
    return agent.send_message(query)
