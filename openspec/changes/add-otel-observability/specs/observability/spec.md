## ADDED Requirements

### Requirement: Inbound WhatsApp turns are traceable
The system SHALL create or propagate an OpenTelemetry trace for each inbound WhatsApp webhook turn and SHALL correlate webhook handling, agent execution, model calls, tool calls, persistence operations, external dependency calls, and Twilio reply delivery under that trace when those operations occur.

#### Scenario: Successful webhook turn creates correlated trace
- **WHEN** Twilio posts a valid WhatsApp webhook and the agent returns a reply
- **THEN** telemetry contains one trace that includes spans for webhook handling, agent execution, any model/tool operations performed, and outbound Twilio reply delivery.

#### Scenario: Invalid webhook still emits request telemetry
- **WHEN** Twilio posts a webhook missing the required sender or body fields
- **THEN** telemetry records the webhook request outcome without creating agent, model, tool, or outbound Twilio spans.

### Requirement: Telemetry uses privacy-safe identifiers
The system SHALL use safe correlation identifiers for telemetry, including OTel trace identifiers, a turn identifier, and a session identifier that does not expose the raw WhatsApp phone number.

#### Scenario: Phone number is not used as telemetry identity
- **WHEN** a WhatsApp webhook is processed for a sender phone number
- **THEN** telemetry attributes include a safe session identifier and do not include the full sender phone number.

#### Scenario: Later Langfuse correlation has shared identifiers
- **WHEN** an agent run emits telemetry
- **THEN** telemetry includes safe turn and session identifiers that can later be copied into Langfuse trace metadata.

### Requirement: Sensitive banking and conversation data is excluded by default
The system MUST NOT emit raw WhatsApp message bodies, assistant replies, account numbers, balances, transaction descriptions, beneficiary details, raw tool inputs, raw tool outputs, Twilio payloads, or Investec payloads in default production telemetry.

#### Scenario: Banking tool succeeds with private data
- **WHEN** a banking tool returns account or transaction data
- **THEN** telemetry records only safe metadata such as tool name, status, duration, result shape, or result count, and does not record the raw banking data.

#### Scenario: Agent receives private user text
- **WHEN** a user sends a WhatsApp message containing private financial context
- **THEN** telemetry records the agent operation metadata without the raw message body.

### Requirement: Semantic spans describe application and agent boundaries
The system SHALL emit low-cardinality semantic spans for meaningful application boundaries, including webhook handling, agent runs, model calls, tool calls, Investec operations, Twilio message sending, and session persistence where implemented.

#### Scenario: Agent calls a tool
- **WHEN** the model requests a registered tool call during an agent run
- **THEN** telemetry contains a tool span with the tool name, status, duration, and error type when applicable.

#### Scenario: External dependency fails
- **WHEN** Investec, Twilio, OpenAI, Cosmos DB, or email delivery fails during a traced operation
- **THEN** telemetry records the failing dependency name, operation name, status, and safe error type under the active trace.

### Requirement: Metrics expose rate, error, and duration signals
The system SHALL emit metrics for request, agent, tool, model, and dependency operations using bounded dimensions suitable for dashboards and alerts.

#### Scenario: Agent run completes
- **WHEN** an agent run completes successfully
- **THEN** metrics record the agent run count and duration with bounded attributes such as environment, model, and status.

#### Scenario: Tool call fails
- **WHEN** a tool call fails
- **THEN** metrics record a tool failure with bounded attributes such as tool name and error type, without user or account identifiers.

### Requirement: Observability remains passive
The system SHALL continue processing webhook and agent workflows when OpenTelemetry export is disabled, unavailable, or misconfigured.

#### Scenario: OTLP endpoint is unavailable
- **WHEN** the configured telemetry export endpoint cannot be reached
- **THEN** the webhook and agent workflow continue according to normal application behavior and telemetry export failure does not change the user-facing reply path.

#### Scenario: Observability is disabled locally
- **WHEN** telemetry is disabled in local development
- **THEN** the application starts and the webhook, agent chat script, and tests can run without requiring a telemetry backend.

### Requirement: Telemetry backend configuration is environment driven
The system SHALL configure service name, environment, resource attributes, sampling, and OTLP export through environment or deployment configuration rather than hard-coded vendor endpoints.

#### Scenario: Deployed container uses OTLP configuration
- **WHEN** the application starts in Azure Container Apps with OTLP environment variables configured
- **THEN** telemetry is exported through the configured OTLP endpoint using the configured service name and resource attributes.

#### Scenario: Vendor backend changes
- **WHEN** telemetry is rerouted from one backend to another OTLP-compatible backend
- **THEN** the change can be made through deployment configuration without changing business logic.
