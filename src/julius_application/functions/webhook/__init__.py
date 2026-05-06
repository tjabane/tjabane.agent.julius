import azure.functions as func
from julius_services.communication.twilio_client import TwilioClient
from julius_application.agent.agent import run

_twilio = TwilioClient()


def main(req: func.HttpRequest) -> func.HttpResponse:
    form = req.form
    number, message = TwilioClient.parse_webhook(form)

    if not number or not message:
        return func.HttpResponse(status_code=400)

    reply = run(whatsapp_number=number, user_message=message)
    _twilio.send_message(to=number, body=reply)

    return func.HttpResponse(status_code=200)
