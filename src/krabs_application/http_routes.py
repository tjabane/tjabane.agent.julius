from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, Response, status

from krabs_agent.agent_runner import run
from krabs_application.health import run_all as run_health_checks
from krabs_observability import create_turn_context_from_env, use_turn_context
from krabs_observability.semantic import AttributeName, SpanName
from krabs_observability.telemetry import record_request_metric, trace_operation
from krabs_services.communication.protocols import MessageSender
from krabs_services.communication.providers import get_message_sender
from krabs_services.communication.twilio_client import parse_webhook

router = APIRouter()
_MESSAGE_SENDER_DEPENDENCY = Depends(get_message_sender)
_WEBHOOK_ATTRS = {
    AttributeName.MESSAGING_PROVIDER,
    AttributeName.OPERATION_NAME,
    AttributeName.SESSION_ID,
    AttributeName.TURN_ID,
}


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
    message_sender: MessageSender = _MESSAGE_SENDER_DEPENDENCY,
) -> None:
    started_at = time.perf_counter()
    http_status_code = status.HTTP_200_OK
    try:
        form = await request.form()
        with trace_operation(
            SpanName.WEBHOOK_PARSE,
            attributes={
                AttributeName.MESSAGING_PROVIDER: "twilio",
                AttributeName.OPERATION_NAME: "webhook.parse",
            },
            allowed_attribute_names=_WEBHOOK_ATTRS,
            emit_metrics=False,
        ) as parse_span:
            number, message = parse_webhook(dict(form))
            turn_context = create_turn_context_from_env(number) if number else None
            if turn_context:
                parse_span.set_attribute(AttributeName.TURN_ID, turn_context.turn_id)
                parse_span.set_attribute(AttributeName.SESSION_ID, turn_context.session_id)
        if not number or not message:
            http_status_code = status.HTTP_400_BAD_REQUEST
            response.status_code = http_status_code
            return None

        assert turn_context is not None
        with use_turn_context(turn_context):
            reply = await asyncio.to_thread(run, whatsapp_number=number, user_message=message)
            await asyncio.to_thread(message_sender.send_message, to=number, body=reply)
        return None
    except Exception:
        http_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        raise
    finally:
        record_request_metric(
            route="/webhook",
            status="error" if http_status_code >= 400 else "success",
            elapsed_seconds=time.perf_counter() - started_at,
            http_status_code=http_status_code,
        )
