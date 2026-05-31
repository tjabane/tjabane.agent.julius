from __future__ import annotations

import os
from pathlib import Path

from openai import OpenAI

from krabs_agent.library.agent import Agent
from krabs_agent.tools.deps import ToolDeps
from krabs_domain.models.agent import Message
from krabs_domain.repositories.agent import SessionRepository
from krabs_services.finance.investec_client import InvestecClient
from krabs_tools.registry import ToolRegistry
from krabs_tools.tools import create_investec_tools

_SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "system.md").read_text()
_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
_sessions: SessionRepository | None = None
_tool_registry: ToolRegistry | None = None


def _get_sessions() -> SessionRepository:
    global _sessions
    if _sessions is None:
        _sessions = SessionRepository()
    return _sessions


def _get_tool_registry() -> ToolRegistry:
    global _tool_registry
    if _tool_registry is None:
        investec_client = InvestecClient()
        registry = ToolRegistry()
        registry.register_many(create_investec_tools(investec_client))
        _tool_registry = registry
    return _tool_registry


def run(
    whatsapp_number: str,
    user_message: str,
    *,
    client: OpenAI | None = None,
    sessions: SessionRepository | None = None,
    tool_deps: ToolDeps | None = None,
) -> str:
    _ = tool_deps
    client = client or OpenAI()
    sessions = sessions or _get_sessions()
    session = sessions.get_or_create(whatsapp_number)

    agent = Agent(
        model=_MODEL,
        system_prompt=_SYSTEM_PROMPT,
        messages=session.messages,
        client=client,
        tool_registry=_get_tool_registry(),
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
    _ = (schedule_id, tool_deps)
    client = client or OpenAI()

    agent = Agent(
        model=_MODEL,
        system_prompt=_SYSTEM_PROMPT,
        client=client,
        tool_registry=_get_tool_registry(),
    )
    return agent.send_message(query)
