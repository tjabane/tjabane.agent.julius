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

The Bicep deployment provisions a Log Analytics workspace and workspace-based Application Insights resource. The Azure Container Apps managed OpenTelemetry agent is configured at the Container Apps environment level and routes application traces and logs to Application Insights.

Azure deployments default `OTEL_MODE` to `otlp`. The Container Apps managed agent injects `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_PROTOCOL`, and `OTEL_RESOURCE_ATTRIBUTES` at runtime. The container app does not set `OTEL_EXPORTER_OTLP_ENDPOINT` itself, so the app exports to the managed agent and the managed agent handles backend routing.

Application Insights currently accepts traces and logs from the managed agent, but not metrics. Custom application metrics are sent only when a custom OTLP destination is configured.

The deployment exposes these OTel parameters:

| Parameter | Environment variable | Default |
|---|---|---|
| `otelMode` | `OTEL_MODE` | `otlp` in Azure deployment, `disabled` in local app defaults |
| `otelServiceName` | `OTEL_SERVICE_NAME` | `mr-krabs` |
| `otelExporterOtlpEndpoint` | managed agent OTLP destination | empty |
| `otelResourceAttributes` | `OTEL_RESOURCE_ATTRIBUTES` | empty; use managed agent injection |
| `otelTracesSampler` | `OTEL_TRACES_SAMPLER` | `parentbased_traceidratio` |
| `otelTracesSamplerArg` | `OTEL_TRACES_SAMPLER_ARG` | `1.0` |

Deploy with Application Insights enabled:

```powershell
.\infrastructure\deploy.ps1 `
  -ResourceGroup "rg-krabs" `
  -Location "southafricanorth"
```

To also route telemetry from the managed agent to another OTLP-compatible backend, pass a custom endpoint:

```powershell
.\infrastructure\deploy.ps1 `
  -ResourceGroup "rg-krabs" `
  -Location "southafricanorth" `
  -OtelExporterOtlpEndpoint "https://otel.example.com:4317"
```

Backend-specific routing, filtering, and redaction should live in the Container Apps managed agent, an external collector, or hosting configuration rather than in business code.

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
