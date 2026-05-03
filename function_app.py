import logging
from datetime import datetime, timedelta, timezone

import azure.functions as func

from agent.agent import run, run_scheduled
from models.reporting import Frequency
from repositories.reporting import ScheduleRepository
from services.twilio_client import TwilioClient

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
