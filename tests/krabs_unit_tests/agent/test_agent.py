from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

from pydantic import BaseModel, ConfigDict

from krabs_agent.agent_runner import run
from krabs_agent.runtime import Agent
from krabs_domain.models.agent import Session
from krabs_tools.registry import ToolRegistry


def _stop_response(content: str, response_id: str = "response_1"):
    return SimpleNamespace(id=response_id, output=[], output_text=content)


def _tool_response(tool_name: str, arguments: str = "{}", call_id: str = "call_1"):
    return SimpleNamespace(
        id="response_with_tool_call",
        output=[
            SimpleNamespace(
                type="function_call",
                name=tool_name,
                arguments=arguments,
                call_id=call_id,
            )
        ],
        output_text="",
    )


class FakeSessions:
    def __init__(self) -> None:
        self._store: dict[str, Session] = {}

    def get_or_create(self, whatsapp_number: str) -> Session:
        if whatsapp_number not in self._store:
            self._store[whatsapp_number] = Session(id=whatsapp_number, whatsapp_number=whatsapp_number)
        return self._store[whatsapp_number]

    def save(self, session: Session) -> Session:
        self._store[session.whatsapp_number] = session
        return session


class ExampleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExampleTool:
    name = "example_tool"
    description = "Example tool."
    input_schema = ExampleInput

    def __init__(self) -> None:
        self.calls = 0

    async def run(self, input_data: ExampleInput) -> list[dict[str, Any]]:
        self.calls += 1
        return [{"id": "1", "name": "Cheque"}]


class TestRun:
    def test_returns_reply_on_stop(self):
        client = MagicMock()
        client.responses.create.return_value = _stop_response("Hello! How can I help?")

        reply = run("+27831234567", "hello", client=client, sessions=FakeSessions())

        assert reply == "Hello! How can I help?"

    def test_appends_user_and_assistant_messages_to_session(self):
        sessions = FakeSessions()
        client = MagicMock()
        client.responses.create.return_value = _stop_response("Hi!")

        run("+27831234567", "hello", client=client, sessions=sessions)

        msgs = sessions._store["+27831234567"].messages
        assert msgs[0].role == "user"
        assert msgs[0].content == "hello"
        assert msgs[-1].role == "assistant"
        assert msgs[-1].content == "Hi!"

    def test_accumulates_messages_across_calls(self):
        sessions = FakeSessions()
        client = MagicMock()
        client.responses.create.return_value = _stop_response("Reply")

        run("+27831234567", "first", client=client, sessions=sessions)
        run("+27831234567", "second", client=client, sessions=sessions)

        msgs = sessions._store["+27831234567"].messages
        assert len(msgs) == 4

    def test_sends_existing_session_messages_to_agent(self):
        sessions = FakeSessions()
        client = MagicMock()
        client.responses.create.return_value = _stop_response("Reply")

        run("+27831234567", "first", client=client, sessions=sessions)
        run("+27831234567", "second", client=client, sessions=sessions)

        second_call_input = client.responses.create.call_args_list[1].kwargs["input"]
        assert second_call_input[-3:] == [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "Reply"},
            {"role": "user", "content": "second"},
        ]

    @patch("krabs_agent.agent_runner.Agent")
    def test_passes_tool_registry_to_agent(self, agent_class):
        client = MagicMock()
        sessions = FakeSessions()
        agent = MagicMock()
        agent.send_message.return_value = "Done."
        agent_class.return_value = agent

        run("+27831234567", "hello", client=client, sessions=sessions)

        assert agent_class.call_args.kwargs["tool_registry"] is not None


class TestAgentToolRegistry:
    def test_dispatches_tool_call_then_continues(self):
        tool = ExampleTool()
        registry = ToolRegistry()
        registry.register(tool)
        client = MagicMock()
        client.responses.create.side_effect = [
            _tool_response("example_tool"),
            _stop_response("You have 1 account.", response_id="response_2"),
        ]
        agent = Agent(
            model="test-model",
            system_prompt="System prompt.",
            client=client,
            tool_registry=registry,
        )

        reply = agent.send_message("show accounts")

        assert reply == "You have 1 account."
        assert tool.calls == 1
        assert client.responses.create.call_count == 2

    def test_sends_function_call_output_to_second_response_call(self):
        tool = ExampleTool()
        registry = ToolRegistry()
        registry.register(tool)
        client = MagicMock()
        client.responses.create.side_effect = [
            _tool_response("example_tool", call_id="call_123"),
            _stop_response("Done.", response_id="response_2"),
        ]
        agent = Agent(
            model="test-model",
            system_prompt="System prompt.",
            client=client,
            tool_registry=registry,
        )

        agent.send_message("accounts")

        second_call = client.responses.create.call_args_list[1].kwargs
        assert second_call["previous_response_id"] == "response_with_tool_call"
        assert second_call["input"] == [
            {
                "type": "function_call_output",
                "call_id": "call_123",
                "output": '[{"id": "1", "name": "Cheque"}]',
            }
        ]

