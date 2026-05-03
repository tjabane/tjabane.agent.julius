import json
import os
from pathlib import Path
from openai import OpenAI
from models.session import Message
from repositories.sessions import SessionRepository
from agent.tools import ALL_DEFINITIONS, dispatch

_client = OpenAI()
_sessions = SessionRepository()
_SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "system.md").read_text()
_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")


def run(whatsapp_number: str, user_message: str) -> str:
    session = _sessions.get_or_create(whatsapp_number)
    session.messages.append(Message(role="user", content=user_message))

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        *[{"role": m.role, "content": m.content} for m in session.messages],
    ]

    while True:
        response = _client.chat.completions.create(
            model=_MODEL,
            tools=ALL_DEFINITIONS,
            messages=messages,
        )

        choice = response.choices[0]

        if choice.finish_reason == "stop":
            reply = choice.message.content or ""
            session.messages.append(Message(role="assistant", content=reply))
            _sessions.save(session)
            return reply

        if choice.finish_reason == "tool_calls":
            messages.append(choice.message)
            for tool_call in choice.message.tool_calls:
                inputs = json.loads(tool_call.function.arguments)
                result = _call_tool(tool_call.function.name, inputs)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })


def run_scheduled(schedule_id: str, query: str) -> str:
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]

    while True:
        response = _client.chat.completions.create(
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
                result = _call_tool(tool_call.function.name, inputs)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })


def _call_tool(name: str, inputs: dict) -> str:
    try:
        return dispatch(name, inputs)
    except Exception as e:
        return f"Error: {e}"
