import json
from unittest.mock import MagicMock
import pytest
from krabs_domain.models.agent import Session
from krabs_agent.agent_runner import run, run_scheduled
from krabs_agent.tools.deps import ToolDeps


# ── Helpers ───────────────────────────────────────────────────────────────────

def _stop_response(content: str):
    choice = MagicMock()
    choice.finish_reason = "stop"
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


def _tool_response(tool_name: str, arguments: dict, tool_id: str = "call_1"):
    tool_call = MagicMock()
    tool_call.id = tool_id
    tool_call.function.name = tool_name
    tool_call.function.arguments = json.dumps(arguments)
    choice = MagicMock()
    choice.finish_reason = "tool_calls"
    choice.message.tool_calls = [tool_call]
    response = MagicMock()
    response.choices = [choice]
    return response


class FakeSessions:
    def __init__(self):
        self._store: dict[str, Session] = {}

    def get_or_create(self, whatsapp_number: str) -> Session:
        if whatsapp_number not in self._store:
            self._store[whatsapp_number] = Session(id=whatsapp_number, whatsapp_number=whatsapp_number)
        return self._store[whatsapp_number]

    def save(self, session: Session) -> Session:
        self._store[session.whatsapp_number] = session
        return session


# ── run() tests ───────────────────────────────────────────────────────────────

class TestRun:
    def test_returns_reply_on_stop(self):
        client = MagicMock()
        client.chat.completions.create.return_value = _stop_response("Hello! How can I help?")

        reply = run("+27831234567", "hello", client=client, sessions=FakeSessions())

        assert reply == "Hello! How can I help?"

    def test_appends_user_and_assistant_messages_to_session(self):
        sessions = FakeSessions()
        client = MagicMock()
        client.chat.completions.create.return_value = _stop_response("Hi!")

        run("+27831234567", "hello", client=client, sessions=sessions)

        msgs = sessions._store["+27831234567"].messages
        assert msgs[0].role == "user"
        assert msgs[0].content == "hello"
        assert msgs[-1].role == "assistant"
        assert msgs[-1].content == "Hi!"

    def test_accumulates_messages_across_calls(self):
        sessions = FakeSessions()
        client = MagicMock()
        client.chat.completions.create.return_value = _stop_response("Reply")

        run("+27831234567", "first", client=client, sessions=sessions)
        run("+27831234567", "second", client=client, sessions=sessions)

        msgs = sessions._store["+27831234567"].messages
        assert len(msgs) == 4  # user, assistant, user, assistant

    def test_dispatches_tool_call_then_continues(self):
        mock_investec = MagicMock()
        mock_investec.get_accounts.return_value = [{"id": "1", "name": "Cheque"}]
        deps = ToolDeps(investec=mock_investec)

        client = MagicMock()
        client.chat.completions.create.side_effect = [
            _tool_response("get_accounts", {}),
            _stop_response("You have 1 account."),
        ]

        reply = run("+27831234567", "show accounts", client=client, sessions=FakeSessions(), tool_deps=deps)

        assert reply == "You have 1 account."
        mock_investec.get_accounts.assert_called_once()
        assert client.chat.completions.create.call_count == 2

    def test_tool_result_appended_before_second_llm_call(self):
        mock_investec = MagicMock()
        mock_investec.get_accounts.return_value = [{"id": "abc"}]
        deps = ToolDeps(investec=mock_investec)

        client = MagicMock()
        client.chat.completions.create.side_effect = [
            _tool_response("get_accounts", {}),
            _stop_response("Done."),
        ]

        run("+27831234567", "accounts", client=client, sessions=FakeSessions(), tool_deps=deps)

        second_call_messages = client.chat.completions.create.call_args_list[1][1]["messages"]
        roles = [m["role"] if isinstance(m, dict) else m.role for m in second_call_messages]
        assert "tool" in roles


# ── run_scheduled() tests ─────────────────────────────────────────────────────

class TestRunScheduled:
    def test_returns_reply_on_stop(self):
        client = MagicMock()
        client.chat.completions.create.return_value = _stop_response("Report done.")

        result = run_scheduled("sched-1", "send balance summary", client=client)

        assert result == "Report done."

    def test_injects_schedule_id_into_send_email(self):
        mock_repo = MagicMock()
        mock_email = MagicMock()
        deps = ToolDeps(report_repo=mock_repo, email=mock_email)

        client = MagicMock()
        client.chat.completions.create.side_effect = [
            _tool_response("send_email", {"subject": "Report", "body": "Balance: R1000"}),
            _stop_response("Done."),
        ]

        run_scheduled("sched-42", "send report", client=client, tool_deps=deps)

        saved_report = mock_repo.save.call_args[0][0]
        assert saved_report.schedule_id == "sched-42"

    def test_does_not_persist_session(self):
        client = MagicMock()
        client.chat.completions.create.return_value = _stop_response("Done.")

        # run_scheduled has no sessions parameter — calling it should not raise
        run_scheduled("sched-1", "query", client=client)
