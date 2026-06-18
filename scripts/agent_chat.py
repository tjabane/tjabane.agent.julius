from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

SYSTEM_PROMPT = (SRC / "krabs_agent" / "prompts" / "system.md").read_text()


def _create_agent():
    from openai import OpenAI

    from krabs_agent.runtime import Agent
    from krabs_domain.repositories.reporting import ReportRepository
    from krabs_observability.adapters import BankingClient as ObservedBankingClient
    from krabs_services.communication import get_report_sender
    from krabs_services.finance.investec_client import InvestecClient
    from krabs_tools.registry import ToolRegistry
    from krabs_tools.tools import create_banking_tools, create_datetime_tools, create_reporting_tools

    banking_client = ObservedBankingClient(InvestecClient())
    tool_registry = ToolRegistry()
    tool_registry.register_many(create_banking_tools(banking_client))
    tool_registry.register_many(create_datetime_tools())
    tool_registry.register_many(create_reporting_tools(get_report_sender(), ReportRepository))

    return Agent(
        model=os.environ.get("OPENAI_MODEL", "gpt-5"),
        system_prompt=SYSTEM_PROMPT,
        client=OpenAI(),
        tool_registry=tool_registry,
    )


def main() -> int:
    load_dotenv(ROOT / ".env")

    from krabs_observability import create_turn_context_from_env, initialize_observability, use_turn_context

    initialize_observability()
    agent = _create_agent()

    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
        with use_turn_context(create_turn_context_from_env("local-agent-chat")):
            print(agent.send_message(message))
        return 0

    print("Agent chat. Type /exit to quit.")
    while True:
        try:
            message = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not message:
            continue
        if message in {"/exit", "/quit"}:
            return 0

        with use_turn_context(create_turn_context_from_env("local-agent-chat")):
            print(f"agent> {agent.send_message(message)}")


if __name__ == "__main__":
    raise SystemExit(main())
