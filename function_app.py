import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import azure.functions as func

from julius_application.agent.agent import run, run_scheduled
from julius_application.health import run_all as run_health_checks
from julius_domain.models.reporting import Frequency
from julius_domain.repositories.reporting import ScheduleRepository
from julius_services.communication.twilio_client import TwilioClient

app = func.FunctionApp()

_twilio: TwilioClient | None = None
_schedules: ScheduleRepository | None = None


def _get_twilio() -> TwilioClient:
    global _twilio
    if _twilio is None:
        _twilio = TwilioClient()
    return _twilio


def _get_schedules() -> ScheduleRepository:
    global _schedules
    if _schedules is None:
        _schedules = ScheduleRepository()
    return _schedules


@app.route(route="ping", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def ping(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}),
        status_code=200,
        mimetype="application/json",
    )


@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    result = run_health_checks()
    status_code = 200 if result["status"] == "healthy" else 503
    return func.HttpResponse(
        body=json.dumps(result),
        status_code=status_code,
        mimetype="application/json",
    )


@app.route(route="webhook", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def webhook(req: func.HttpRequest) -> func.HttpResponse:
    number, message = TwilioClient.parse_webhook(dict(req.form))
    if not number or not message:
        return func.HttpResponse(status_code=400)
    reply = run(whatsapp_number=number, user_message=message)
    _get_twilio().send_message(to=number, body=reply)
    return func.HttpResponse(status_code=200)


@app.timer_trigger(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=False)
def scheduler(timer: func.TimerRequest) -> None:
    due = _get_schedules().list_due()
    for schedule in due:
        try:
            run_scheduled(schedule_id=schedule.id, query=schedule.query)
            schedule.next_run = _next_run(schedule.frequency)
            _get_schedules().save(schedule)
        except Exception as e:
            logging.error("Scheduled run failed for %s: %s", schedule.id, e)


def _next_run(frequency: Frequency) -> datetime:
    base = datetime.now(timezone.utc).replace(hour=6, minute=0, second=0, microsecond=0)
    if frequency == Frequency.DAILY:
        return base + timedelta(days=1)
    return base + timedelta(weeks=1)
