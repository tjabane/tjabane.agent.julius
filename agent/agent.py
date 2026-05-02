from pathlib import Path
from anthropic import Anthropic
from models.session import Message, Session
from repositories.sessions import SessionRepository
from agent.tools import ALL_DEFINITIONS, dispatch

_client = Anthropic()
_sessions = SessionRepository()
_SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "system.md").read_text()
_MODEL = "claude-sonnet-4-6"


def run(whatsapp_number: str, user_message: str) -> str:
    session = _sessions.get_or_create(whatsapp_number)
    session.messages.append(Message(role="user", content=user_message))

    messages = [{"role": m.role, "content": m.content} for m in session.messages]

    while True:
        response = _client.messages.create(
            model=_MODEL,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            tools=ALL_DEFINITIONS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            reply = _extract_text(response)
            session.messages.append(Message(role="assistant", content=reply))
            _sessions.save(session)
            return reply

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = _call_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "user", "content": tool_results})


def run_scheduled(schedule_id: str, query: str) -> str:
    """Run the agent for a scheduled report with no session context."""
    messages = [{"role": "user", "content": query}]

    while True:
        response = _client.messages.create(
            model=_MODEL,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            tools=ALL_DEFINITIONS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return _extract_text(response)

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    inputs = dict(block.input)
                    if block.name == "send_email":
                        inputs["schedule_id"] = schedule_id
                    result = _call_tool(block.name, inputs)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "user", "content": tool_results})


def _call_tool(name: str, inputs: dict) -> str:
    try:
        return dispatch(name, inputs)
    except Exception as e:
        return f"Error: {e}"


def _extract_text(response) -> str:
    for block in response.content:
        if hasattr(block, "text"):
            return block.text
    return ""
