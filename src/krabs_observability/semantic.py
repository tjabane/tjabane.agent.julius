from __future__ import annotations

from collections.abc import Mapping, Set

type SafeAttributeValue = str | bool | int | float


class SpanName:
    WEBHOOK_PARSE = "twilio.webhook.parse"
    AGENT_RUN = "agent.run"
    MODEL_CALL = "openai.responses.create"
    TOOL_CALL = "tool.call"
    INVESTEC_OPERATION = "investec.operation"
    TWILIO_SEND = "twilio.message.send"
    SESSION_LOAD = "session.load"
    SESSION_SAVE = "session.save"


class MetricName:
    REQUEST_COUNT = "krabs.request.count"
    REQUEST_DURATION = "krabs.request.duration"
    AGENT_RUN_COUNT = "krabs.agent.run.count"
    AGENT_RUN_DURATION = "krabs.agent.run.duration"
    MODEL_CALL_COUNT = "krabs.model.call.count"
    MODEL_CALL_DURATION = "krabs.model.call.duration"
    TOOL_CALL_COUNT = "krabs.tool.call.count"
    TOOL_CALL_DURATION = "krabs.tool.call.duration"
    DEPENDENCY_OPERATION_COUNT = "krabs.dependency.operation.count"
    DEPENDENCY_OPERATION_DURATION = "krabs.dependency.operation.duration"


class AttributeName:
    TURN_ID = "turn.id"
    SESSION_ID = "session.id"
    AGENT_MODEL = "agent.model"
    TOOL_NAME = "tool.name"
    DEPENDENCY_NAME = "dependency.name"
    OPERATION_NAME = "operation.name"
    MESSAGING_PROVIDER = "messaging.provider"
    HTTP_STATUS_CODE = "http.status_code"
    STATUS = "status"
    ERROR_TYPE = "error.type"
    RESULT_KIND = "result.kind"
    RESULT_COUNT = "result.count"


FORBIDDEN_ATTRIBUTE_NAMES = frozenset(
    {
        "message.body",
        "assistant.reply",
        "phone.number",
        "account.number",
        "account.balance",
        "transaction.description",
        "beneficiary.detail",
        "raw.tool.input",
        "raw.tool.output",
        "twilio.payload",
        "investec.payload",
    }
)


def safe_attributes(
    attributes: Mapping[str, object],
    *,
    allowed_names: Set[str],
) -> dict[str, SafeAttributeValue]:
    return {
        name: value
        for name, value in attributes.items()
        if name in allowed_names
        and name not in FORBIDDEN_ATTRIBUTE_NAMES
        and isinstance(value, str | bool | int | float)
    }
