from __future__ import annotations
import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Response, status
from julius_application.agent.agent import run
from julius_application.health import run_all as run_health_checks
from julius_application.observability import (
    configure_observability,
    hash_identifier,
    mark_success,
    set_attributes,
    start_span,
)
from julius_application.scheduler import run_scheduler_loop
from julius_services.communication.twilio_client import TwilioClient

_twilio: TwilioClient | None = None


def _get_twilio() -> TwilioClient:
    global _twilio
    if _twilio is None:
        _twilio = TwilioClient()
    return _twilio


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_observability()
    scheduler_enabled = os.environ.get("SCHEDULER_ENABLED", "true").lower() == "true"
    stop_event = asyncio.Event()
    scheduler_task: asyncio.Task | None = None
    if scheduler_enabled:
        interval = int(os.environ.get("SCHEDULER_INTERVAL_SECONDS", "300"))
        scheduler_task = asyncio.create_task(
            run_scheduler_loop(interval_seconds=interval, stop_event=stop_event)
        )

    try:
        yield
    finally:
        stop_event.set()
        if scheduler_task:
            scheduler_task.cancel()
            try:
                await scheduler_task
            except asyncio.CancelledError:
                pass


app = FastAPI(title="Julius", version="0.1.0", lifespan=lifespan)


@app.get("/ping")
@app.get("/api/ping", include_in_schema=False)
async def ping() -> dict[str, str]:
    with start_span("http.ping", {"app.operation": "ping"}) as span:
        mark_success(span)
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/health")
@app.get("/api/health", include_in_schema=False)
async def health(response: Response) -> dict:
    with start_span("http.health", {"app.operation": "health"}) as span:
        result = await asyncio.to_thread(run_health_checks)
        status_code = status.HTTP_200_OK if result["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
        response.status_code = status_code
        set_attributes(span, {
            "health.status": result["status"],
            "http.response.status_code": status_code,
        })
        if status_code == status.HTTP_200_OK:
            mark_success(span)
        else:
            span.set_attribute("app.status", "failure")
        return result


@app.post("/webhook", status_code=status.HTTP_200_OK)
@app.post("/api/webhook", status_code=status.HTTP_200_OK, include_in_schema=False)
async def webhook(request: Request, response: Response) -> None:
    with start_span("webhook.receive", {"messaging.system": "twilio"}) as span:
        form = await request.form()
        number, message = TwilioClient.parse_webhook(dict(form))
        set_attributes(span, {"user.hash": hash_identifier(number)})
        if not number or not message:
            response.status_code = status.HTTP_400_BAD_REQUEST
            span.set_attribute("http.response.status_code", status.HTTP_400_BAD_REQUEST)
            span.set_attribute("app.status", "invalid_request")
            return None

        reply = await asyncio.to_thread(run, whatsapp_number=number, user_message=message)
        await asyncio.to_thread(_get_twilio().send_message, to=number, body=reply)
        span.set_attribute("http.response.status_code", status.HTTP_200_OK)
        mark_success(span)
        return None
