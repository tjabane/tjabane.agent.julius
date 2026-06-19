# Observability

Mr Krabs uses OpenTelemetry for application traces, metrics, and log correlation. Telemetry is passive: webhook and agent behavior must keep working when observability is disabled or an exporter is unavailable.

## Local Modes

Set `OTEL_MODE` in `.env`:

| Mode | Use |
|---|---|
| `disabled` | Default local mode. The app starts with no exporter and uses no-op OTel providers. |
| `console` | Debug mode. Spans and metrics are printed to stdout for local inspection. |
| `otlp` | Export traces and metrics to an OTLP endpoint such as a local OpenTelemetry Collector. |

Example console mode:

```powershell
$env:OTEL_MODE="console"
uv run uvicorn krabs_application.fastapi_app:app --app-dir src --reload --port 8000
```

Example OTLP mode:

```powershell
$env:OTEL_MODE="otlp"
$env:OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
$env:OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
uv run uvicorn krabs_application.fastapi_app:app --app-dir src --reload --port 8000
```

`scripts/agent_chat.py` uses the same observability initialization as the API. In console or OTLP mode it emits the same safe agent, model, tool, dependency, and session spans under a local safe session identity.

## Azure Container Apps

The Bicep deployment exposes OTel configuration as parameters and passes them to the Container App:

| Parameter | Environment variable | Default |
|---|---|---|
| `otelMode` | `OTEL_MODE` | `disabled` |
| `otelServiceName` | `OTEL_SERVICE_NAME` | `mr-krabs` |
| `otelExporterOtlpEndpoint` | `OTEL_EXPORTER_OTLP_ENDPOINT` | empty |
| `otelResourceAttributes` | `OTEL_RESOURCE_ATTRIBUTES` | `deployment.environment=<appEnvironment>,service.namespace=krabs` |
| `otelTracesSampler` | `OTEL_TRACES_SAMPLER` | `parentbased_traceidratio` |
| `otelTracesSamplerArg` | `OTEL_TRACES_SAMPLER_ARG` | `1.0` |

Deploy with OTLP enabled by passing parameters to the deployment script or underlying Bicep command, for example:

```powershell
.\infrastructure\deploy.ps1 `
  -ResourceGroup "rg-krabs" `
  -Location "southafricanorth" `
  -OtelMode "otlp" `
  -OtelExporterOtlpEndpoint "http://otel-collector:4317"
```

The application exports through OTLP only. Backend-specific routing, filtering, and redaction should live in the collector or hosting configuration rather than in business code.

## Privacy Contract

Telemetry may include bounded operational attributes such as `status`, `error.type`, `agent.model`, `tool.name`, `dependency.name`, `operation.name`, `http.status_code`, `turn.id`, and `session.id`.

Telemetry must not include raw WhatsApp message bodies, assistant replies, phone numbers, banking payloads, account numbers, balances, transaction descriptions, beneficiary details, raw tool inputs, or raw tool outputs.

Metrics intentionally omit `turn.id` and `session.id` to avoid high-cardinality dimensions. Those identifiers are trace attributes only.

## Future Langfuse Correlation

Langfuse is not implemented in this change. A later Langfuse integration can correlate LLM-native traces with OpenTelemetry by copying safe metadata from the active OTel context:

- `turn.id`
- `session.id`
- OTel trace ID
- OTel span ID when attaching a generation or tool observation to a specific operation
- `agent.model`
- environment and service name resource attributes

Langfuse should continue the same privacy contract: no raw WhatsApp body, assistant reply, banking payload, account number, balance, beneficiary detail, transaction description, raw tool input, or raw tool output by default.
