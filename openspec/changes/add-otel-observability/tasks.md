## 1. Dependencies and Configuration

- [x] 1.1 Add OpenTelemetry Python dependencies for API, SDK, OTLP export, FastAPI/ASGI instrumentation, HTTP client instrumentation, and logging correlation.
- [x] 1.2 Add environment configuration examples for enabling, disabling, sampling, service name, resource attributes, and OTLP endpoint settings.
- [x] 1.3 Ensure the package/build configuration includes any new observability package or module paths.

## 2. Observability Foundation

- [ ] 2.1 Create a neutral observability module for OTel initialization, tracer/meter access, safe attribute helpers, and no-op behavior when disabled.
- [ ] 2.2 Define constants or helpers for approved span names, metric names, safe attribute names, and forbidden sensitive telemetry fields.
- [ ] 2.3 Implement safe turn/session identity helpers that avoid raw WhatsApp phone numbers and can be reused by the webhook and agent paths.
- [ ] 2.4 Add unit tests for disabled/no-op telemetry initialization and safe identifier generation.

## 3. Application and Dependency Instrumentation

- [ ] 3.1 Wire OTel initialization into FastAPI application startup without changing route behavior.
- [ ] 3.2 Enable FastAPI/ASGI request tracing and verify invalid webhooks produce request telemetry without agent spans.
- [ ] 3.3 Add webhook turn correlation so valid inbound WhatsApp turns carry safe `turn.id` and `session.id` metadata.
- [ ] 3.4 Add semantic spans for Twilio webhook parsing and outbound Twilio message sending.
- [ ] 3.5 Add dependency spans or safe attributes for Investec operations and provider failures where auto-instrumentation is insufficient.
- [ ] 3.6 Add optional session persistence spans for load/save operations if they provide useful visibility without leaking stored message content.

## 4. Agent and Tool Instrumentation

- [ ] 4.1 Add an `agent.run` span around each agent turn with safe model, status, duration, turn, and session attributes.
- [ ] 4.2 Add model-call spans or safe attributes around `OpenAI.responses.create` calls when the OpenAI SDK/HTTP spans do not provide sufficient semantic clarity.
- [ ] 4.3 Add `tool.call` spans around registered tool execution with tool name, status, duration, result shape/count where safe, and safe error type.
- [ ] 4.4 Ensure tool telemetry excludes raw tool arguments, raw tool outputs, banking payloads, account numbers, balances, beneficiaries, and transaction descriptions.
- [ ] 4.5 Ensure the local `scripts/agent_chat.py` path uses the same safe observability setup or a documented local no-op/console mode.

## 5. Metrics and Logs

- [ ] 5.1 Add request, agent run, model call, tool call, and dependency operation RED metrics using bounded dimensions only.
- [ ] 5.2 Add log correlation with active trace/span identifiers for notable application errors without turning logs into the primary trace structure.
- [ ] 5.3 Add unit tests proving metric/log attributes do not include raw phone numbers, message bodies, or banking payload fields.

## 6. Infrastructure and Documentation

- [ ] 6.1 Document local telemetry modes: disabled, console/debug, and OTLP endpoint.
- [ ] 6.2 Update deployment documentation for Azure Container Apps OTLP environment variables and resource attributes.
- [ ] 6.3 Add or update infrastructure configuration for OTLP endpoint/resource settings only if needed by the selected deployment path.
- [ ] 6.4 Document how Langfuse can later correlate with OTel using shared `turn.id`, `session.id`, and OTel trace metadata without implementing Langfuse now.

## 7. Verification

- [ ] 7.1 Add focused unit tests for webhook trace correlation, invalid webhook behavior, agent span behavior, tool span behavior, and passive disabled mode.
- [ ] 7.2 Add a privacy regression test that fails if forbidden sensitive fields appear in emitted telemetry records.
- [ ] 7.3 Run `uv run ruff format --check .`, `uv run ruff check .`, `uv run pyright`, and `uv run pytest`.
- [ ] 7.4 Manually verify a local webhook or `scripts/agent_chat.py` run with console/OTLP telemetry and confirm traces show the expected span hierarchy.
