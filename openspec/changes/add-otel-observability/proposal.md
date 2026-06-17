## Why

Mr Krabs needs production-grade observability so a WhatsApp banking turn can be debugged after the fact without exposing private banking or conversation content. The first step should establish a clean OpenTelemetry foundation for application causality, latency, dependency failures, and trace/log correlation before adding LLM-specific tracing such as Langfuse.

## What Changes

- Add an OpenTelemetry-based observability foundation for the FastAPI webhook, agent runner, tool execution, and external dependency boundaries.
- Define a privacy-first telemetry contract that forbids raw WhatsApp message bodies, banking payloads, account numbers, balances, beneficiary details, transaction descriptions, and full phone numbers in telemetry by default.
- Introduce stable trace identity for each inbound WhatsApp turn, with safe session/turn correlation fields that can later be shared with Langfuse.
- Emit semantic spans and metrics for application operations such as webhook handling, agent runs, model calls, tool calls, Investec operations, Twilio sends, and session persistence.
- Route telemetry through OTLP/OpenTelemetry Collector configuration rather than coupling application code directly to a vendor backend.
- Document Langfuse as a later integration point for LLM-native generations, prompt/version metadata, evaluations, and agent behavior analysis; this change does not implement Langfuse.

## Capabilities

### New Capabilities
- `observability`: Application telemetry requirements for OpenTelemetry traces, metrics, log correlation, privacy-safe attributes, and future Langfuse correlation.

### Modified Capabilities

## Impact

- Affected runtime paths: `krabs_application` FastAPI app/webhook, `krabs_agent` runner/runtime, `krabs_tools` tool dispatch, `krabs_services` Investec/Twilio/email integrations, and Cosmos-backed session/report repositories where persistence spans are useful.
- Affected infrastructure: container runtime configuration, environment variables, and deployment configuration for OTLP export and optional OpenTelemetry Collector routing.
- Affected dependencies: OpenTelemetry Python API/SDK/instrumentation packages and OTLP exporter packages.
- Safety impact: no money movement behavior changes; no user-facing WhatsApp copy changes; personal financial data handling becomes more explicit through a telemetry redaction contract.
- Future integration impact: Langfuse can later attach to the same turn/session identifiers and active trace context without replacing the OTel application trace spine.
