## Context

Mr Krabs currently has a compact runtime path: Twilio posts a WhatsApp webhook to FastAPI, the route parses the message, `krabs_agent.agent_runner.run` drives the OpenAI Responses API loop, registered tools call services such as Investec and reporting/email, the session is persisted, and Twilio receives the reply to send back to the user. When failures or surprising agent behavior occur, the system needs a way to reconstruct the application path without storing raw banking or conversation content.

This design establishes OpenTelemetry as the application observability spine. OTel will describe request causality, operation boundaries, dependency latency, errors, and trace/log correlation. Langfuse remains a later integration for LLM-native generations, prompt versions, evaluations, and richer agent behavior analysis, correlated through shared trace/turn/session identifiers.

## Goals / Non-Goals

**Goals:**

- Create one OTel trace per inbound WhatsApp turn, spanning webhook handling, agent execution, tool dispatch, external dependencies, persistence, and Twilio reply.
- Preserve Clean Architecture boundaries by keeping telemetry helpers neutral and injecting or importing instrumentation only at application, agent, tool, and service boundaries.
- Define stable semantic span names and low-cardinality attributes for application, agent, tool, and dependency operations.
- Enforce a privacy-first telemetry contract that excludes raw messages, raw tool inputs/outputs, banking payloads, account numbers, balances, transaction descriptions, beneficiary details, and full phone numbers by default.
- Export traces and metrics via OTLP so deployment can route telemetry through an OpenTelemetry Collector or vendor-specific endpoint without hard-coding a backend.
- Prepare for later Langfuse correlation by carrying safe `turn_id`, `session_id`, and OTel trace identifiers through agent execution.

**Non-Goals:**

- Do not implement Langfuse in this change.
- Do not capture raw prompt, completion, WhatsApp body, or banking payload content in production telemetry.
- Do not change money movement behavior, confirmation rules, user-facing WhatsApp copy, or agent tool schemas except where instrumentation wrappers require safe metadata.
- Do not build dashboards, alert rules, or production SLOs in this change.
- Do not make observability availability part of the user request success path.

## Decisions

### Use OTel as the application trace spine

The application will initialize OpenTelemetry once during application startup and use the active OTel context across FastAPI routes, agent execution, tool calls, and services. Auto-instrumentation can cover ASGI/FastAPI and outbound HTTP libraries where practical, while manual spans define domain operations that auto-instrumentation cannot understand.

Alternative considered: use Langfuse as the primary trace system from the start. This was rejected for the first change because Langfuse is strongest for LLM-native behavior, while the immediate foundation needs app/dependency causality across Twilio, FastAPI, tools, Investec, Cosmos, and email.

### Export through OTLP and prefer a Collector boundary

The application will use OTLP exporters and environment-driven configuration. In deployed environments, telemetry should be routed to an OpenTelemetry Collector or equivalent OTLP endpoint. The app should not encode Azure Monitor, Langfuse, or any other backend as business logic.

Alternative considered: direct vendor SDK/exporter setup in application code. This was rejected because it makes vendor migration, sampling, filtering, and redaction harder to centralize.

### Combine auto-instrumentation with boundary instrumentation

Auto-instrumentation will be used for framework and library-level mechanics such as HTTP server/client spans. Manual spans will be added only at meaningful domain boundaries:

- `twilio.webhook.parse`
- `agent.run`
- `openai.responses.create` when SDK auto-instrumentation does not produce a useful semantic boundary
- `tool.call`
- `investec.operation`
- `twilio.message.send`
- `session.load` / `session.save` where persistence visibility is useful

Alternative considered: manual spans everywhere. This was rejected because broad manual tracing increases maintenance cost and noise without adding semantic value.

### Prefer decorators and adapters for custom instrumentation

Custom instrumentation will be concentrated in boundary decorators, adapters, and wrapper services rather than inline `with start_span(...)` blocks spread through route, agent, tool, and service business logic. The observability module will own span creation, status/error recording, metrics emission, and safe attribute construction. Business code should continue to call normal interfaces wherever practical.

Expected wrapper points:

- FastAPI: OTel middleware/auto-instrumentation plus minimal webhook correlation setup.
- Agent execution: an instrumented runner boundary around `agent.run` semantics.
- Tool dispatch: registered `Tool` instances wrapped by an `InstrumentedTool` decorator so `Agent.send_message` can keep calling `tool.run(...)`.
- External providers: instrumented adapters for Twilio/email/Investec public operations where auto-instrumented HTTP spans are not semantically clear enough.
- Persistence: optional repository decorators for `session.load` / `session.save` if persistence visibility is included in the first implementation.

This keeps OTel passive at call sites: disabling telemetry should not require business code changes, and most application code should not import OpenTelemetry directly. Inline context managers remain acceptable inside the observability facade or wrapper classes, where they are isolated from domain behavior and privacy rules can be enforced centrally.

### Use stable names and safe attributes

Span names will be low-cardinality and stable. Variable detail belongs in attributes only when it is safe and bounded. Examples:

- `tool.name`
- `agent.model`
- `dependency.name`
- `operation.name`
- `messaging.provider`
- `http.status_code`
- `error.type`
- `turn.id`
- `session.id`

Forbidden attributes include raw user messages, assistant replies, phone numbers, account numbers, balances, transaction descriptions, beneficiary details, raw tool inputs, raw tool outputs, Twilio payloads, and Investec payloads.

Alternative considered: capture raw inputs/outputs and rely on backend redaction. This was rejected because banking telemetry should be private before export, not only after ingestion.

### Keep observability passive

Telemetry creation and export must be best-effort. If the SDK is disabled, misconfigured, or unable to export, webhook handling and agent execution must continue. Instrumentation code should fail closed by dropping telemetry rather than raising user-visible failures.

Alternative considered: require exporter availability during startup. This was rejected because observability is operational support, not a prerequisite for replying to WhatsApp.

### Prepare but do not couple to Langfuse

The OTel layer will expose enough safe context for later Langfuse integration: OTel trace ID, turn ID, session ID, environment, version, agent model, and operation names. Langfuse can later add LLM-native observations under the same turn/session identity using its OpenAI wrapper or explicit observations.

Alternative considered: add Langfuse OpenAI wrapping in the same change. This was rejected to keep the first change focused and to verify OTel privacy/correlation behavior independently.

## Risks / Trade-offs

- Sensitive data leakage through auto-instrumentation -> Disable or configure request/response payload capture, test telemetry output, and enforce a forbidden-attribute contract in unit tests.
- High-cardinality metrics from user/session identifiers -> Keep metrics dimensions limited to route, status, dependency, operation, tool name, model, and error type; use trace attributes for safe correlation instead of metric labels.
- Trace noise from library auto-instrumentation -> Start with a narrow set of instrumentations and add manual spans for semantic clarity.
- Exporter failures affecting user replies -> Use standard OTel best-effort exporters and avoid custom synchronous network calls in the request path.
- Local/deployed behavior drift -> Support a local console/no-op configuration and production OTLP configuration through the same initialization path.
- Later Langfuse duplication -> Treat OTel as the app spine and Langfuse as the LLM layer; share identifiers instead of trying to make both systems own the same concerns.

## Migration Plan

1. Add OTel dependencies and a neutral observability module that configures tracing, metrics, resource attributes, and safe context helpers.
2. Enable framework/library instrumentation for FastAPI/ASGI and outbound HTTP only after verifying payload capture behavior.
3. Add manual spans and metrics at the agreed semantic boundaries.
4. Add tests that verify request/turn/session correlation and forbidden sensitive fields.
5. Add local/deployed environment documentation for no-op/console/OTLP export modes.
6. Add infrastructure configuration for OTLP endpoint/resource attributes where needed.
7. Roll back by disabling telemetry through environment configuration; the app must continue to serve requests without code changes.

## Open Questions

- Which backend should receive OTel data first: Azure Monitor/Application Insights, a local Collector pipeline, or another OTLP-compatible target?
- Should production sampling start at 100% while the app is single-user, or should it immediately use a lower default with error-biased retention?
- Should Cosmos repository spans be included in the first implementation, or deferred until repository latency/errors become a known debugging need?
- Which exact OpenAI Responses API metadata is safe and useful to attach before Langfuse is introduced?
