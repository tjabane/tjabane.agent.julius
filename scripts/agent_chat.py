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
    from krabs_agent.library.agent import Agent
    from krabs_agent.tools import ALL_DEFINITIONS

    return Agent(
        model=os.environ.get("OPENAI_MODEL", "gpt-5"),
        system_prompt=SYSTEM_PROMPT,
        tools=ALL_DEFINITIONS,
    )


def main() -> int:
    load_dotenv(ROOT / ".env")

    agent = _create_agent()

    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
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

        print(f"agent> {agent.send_message(message)}")


if __name__ == "__main__":
    raise SystemExit(main())
