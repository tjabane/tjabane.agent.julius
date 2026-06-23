from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

from scripts import agent_chat


def test_agent_chat_initializes_observability_and_uses_local_turn_context(monkeypatch, capsys) -> None:
    calls = []

    class FakeAgent:
        def send_message(self, message: str) -> str:
            calls.append(("send_message", message))
            return "agent reply"

    @contextmanager
    def fake_use_turn_context(turn_context):
        calls.append(("use_turn_context", turn_context))
        yield

    monkeypatch.setattr(agent_chat, "load_dotenv", lambda path: calls.append(("load_dotenv", path)))
    monkeypatch.setattr(agent_chat, "_create_agent", lambda: FakeAgent())
    monkeypatch.setattr(
        "krabs_observability.initialize_observability",
        lambda: calls.append(("initialize_observability", None)),
    )
    monkeypatch.setattr(
        "krabs_observability.create_turn_context_from_env",
        lambda identity: SimpleNamespace(turn_id="turn-1", session_id=f"safe-{identity}"),
    )
    monkeypatch.setattr("krabs_observability.use_turn_context", fake_use_turn_context)
    monkeypatch.setattr("sys.argv", ["agent_chat.py", "hello"])

    assert agent_chat.main() == 0

    assert ("initialize_observability", None) in calls
    assert ("use_turn_context", SimpleNamespace(turn_id="turn-1", session_id="safe-local-agent-chat")) in calls
    assert ("send_message", "hello") in calls
    assert "agent reply" in capsys.readouterr().out
