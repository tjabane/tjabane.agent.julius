from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Annotated, Protocol

from fastapi import APIRouter, Depends, Request, Response, status

from krabs_agent.agent_runner import run
from krabs_application.health import run_all as run_health_checks
from krabs_services.communication.protocols import MessageSender
from krabs_services.communication.providers import get_message_sender
from krabs_services.communication.twilio_client import parse_webhook

router = APIRouter()


class AgentRunner(Protocol):
    def __call__(self, whatsapp_number: str, user_message: str) -> str:
        ...


def get_agent_runner() -> AgentRunner:
    return run


@router.get("/ping")
@router.get("/api/ping", include_in_schema=False)
async def ping() -> dict[str, str]:
    return {"status": "ok", "timestamp": datetime.now(UTC).isoformat()}


@router.get("/health")
@router.get("/api/health", include_in_schema=False)
async def health(response: Response) -> dict:
    result = await asyncio.to_thread(run_health_checks)
    response.status_code = status.HTTP_200_OK if result["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return result


@router.post("/webhook", status_code=status.HTTP_200_OK)
@router.post("/api/webhook", status_code=status.HTTP_200_OK, include_in_schema=False)
async def webhook(
    request: Request,
    response: Response,
    agent_runner: Annotated[AgentRunner, Depends(get_agent_runner)],
    message_sender: Annotated[MessageSender, Depends(get_message_sender)],
) -> None:
    form = await request.form()
    number, message = parse_webhook(dict(form))
    if not number or not message:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return None

    reply = await asyncio.to_thread(agent_runner, whatsapp_number=number, user_message=message)
    await asyncio.to_thread(message_sender.send_message, to=number, body=reply)
    return None
