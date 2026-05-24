# Mr Krabs Use Cases

Mr Krabs is a WhatsApp-first Investec banking assistant for one user. The user speaks in plain English, the assistant resolves the request, calls the relevant banking, memory, reporting, or scheduling tools, and replies back through WhatsApp.

The stories below describe the current product behavior as implemented today.

See [use-case-diagrams.md](use-case-diagrams.md) for diagram views of these stories and their supporting systems.

## Cast

- **User**: The Investec account holder using WhatsApp.
- **Mr Krabs**: The AI banking assistant. It is concise, protective of the user's money, and uses a light Mr Krabs-style voice.
- **Investec API**: Source of account, balance, transaction, beneficiary, transfer, payment, and document data.
- **Cosmos DB**: Stores chat sessions, memories, skills, schedules, and sent report records.
- **Twilio WhatsApp**: Receives user messages and delivers replies.
- **Azure Communication Services Email**: Sends generated financial reports by email.
- **Scheduler**: Runs every five minutes when enabled and dispatches due scheduled reports.

## Story 1: Checking What Money Is Available

Thabo is standing in a store and wants to know whether he can afford a purchase without dipping into money already committed elsewhere. He sends:

> "How much is available in my cheque account?"

Mr Krabs retrieves the user's accounts if it needs to identify the right account, then checks the selected account balance. The reply summarizes the available, current, and cash balance in plain language and warns the user if the available amount suggests caution.

**Primary flow**

1. Twilio posts the WhatsApp message to `POST /webhook`.
2. The app parses the sender and message body.
3. The agent loads the existing session for that WhatsApp number.
4. The agent calls `get_accounts` if the account is ambiguous.
5. The agent calls `get_balance` with the chosen account ID.
6. The app sends the final response back over WhatsApp.
7. The conversation is saved to the session store.

**Current capabilities used**

- List accounts.
- Fetch current, available, and cash balances.
- Preserve conversation context for follow-up questions.

**Example follow-up**

> "What about my credit card?"

Because the chat session is retained, Mr Krabs can treat this as a continuation and check the other account without making the user restate the whole request.

## Story 2: Understanding Recent Spending

Naledi notices that her balance is lower than expected. She sends:

> "Show me my card transactions from last week, including pending ones."

Mr Krabs resolves "last week" into concrete Johannesburg dates before asking Investec for transactions. It includes pending transactions when requested, then replies with a concise view of the relevant spend and highlights anything unusual or expensive.

**Primary flow**

1. The agent calls `resolve_date_range` for `last_week`.
2. It identifies the relevant account.
3. It calls `get_transactions` with `from_date`, `to_date`, an optional transaction type, and `include_pending`.
4. It summarizes the returned transactions for WhatsApp.

**Current capabilities used**

- Resolve relative dates such as today, yesterday, this week, last month, last 30 days, and year to date.
- Filter account transactions by date range.
- Filter by transaction type when provided.
- Include or exclude pending transactions.

**Outcome**

The user gets a quick explanation of where the money went without opening the banking app or manually filtering statements.

## Story 3: Paying a Saved Beneficiary

Sipho needs to pay rent to a saved beneficiary. He sends:

> "Pay R8,500 to Rent from my cheque account. Use May rent as my reference."

Mr Krabs first lists beneficiaries if it needs to find the right beneficiary ID. Because payments move money out of the account, it must confirm before executing the payment. It explains the amount, source account, beneficiary, and references, then waits for the user's approval.

**Primary flow**

1. The agent identifies the source account.
2. The agent calls `get_beneficiaries` to match the saved beneficiary and category.
3. Mr Krabs asks the user to confirm the payment details.
4. After confirmation, the agent calls `pay_beneficiary`.
5. Mr Krabs reports whether the payment request was accepted.

**Current capabilities used**

- List saved beneficiaries and beneficiary categories.
- Pay one or more beneficiaries from an account.
- Require confirmation before payment execution.

**Guardrail**

Mr Krabs must not execute beneficiary payments without explicit confirmation from the user.

## Story 4: Moving Money Between Own Accounts

The user wants to move money from one Investec account to another before a debit order runs. They send:

> "Move R2,000 from savings to cheque."

Mr Krabs resolves the source and destination accounts, checks that the transfer details are clear, and asks for confirmation. Once confirmed, it submits the transfer request to Investec.

**Primary flow**

1. The agent calls `get_accounts` to resolve account IDs.
2. It prepares a transfer list with destination account ID, amount, and references.
3. Mr Krabs confirms the transfer with the user.
4. The agent calls `transfer_funds`.
5. The result is summarized back to the user.

**Current capabilities used**

- List Investec accounts.
- Transfer funds to one or more Investec accounts.
- Confirm before money movement.

**Outcome**

The user can rebalance accounts conversationally while still having a confirmation checkpoint before funds move.

## Story 5: Getting Statements or Tax Certificates

The user is preparing documents for an accountant and sends:

> "Find my statements for the last three months."

Mr Krabs identifies the account and date range, retrieves available documents, and explains what is available. If the user asks for a specific document type and date, it retrieves that document through the Investec document endpoint.

**Primary flow**

1. The agent resolves the requested date range.
2. It identifies the account.
3. It calls `get_documents` with `from_date` and `to_date`.
4. If a specific document is requested, it calls `get_documents` with `document_type` and `document_date`.
5. It replies with the document availability or retrieval result.

**Current capabilities used**

- List account documents for a date range.
- Retrieve a specific statement or tax certificate.
- Resolve natural language dates before querying documents.

## Story 6: Creating a Once-Off Financial Report

The user wants a quick spending review before payday:

> "Give me a report on my spending this month and email it to me."

Mr Krabs resolves the month-to-date period, gathers account and transaction data, structures a report with totals and notable items, sends it by email, and saves the report record.

**Primary flow**

1. The agent calls `resolve_date_range` for `this_month`.
2. It calls account and transaction tools needed for the report.
3. It drafts the report with totals, categories, and notable transactions.
4. It calls `send_email` with the subject and plain-text report body.
5. The report is saved and delivered by email.

**Current capabilities used**

- Generate report content from banking data.
- Email financial reports.
- Save sent report records.
- Use saved skills when a relevant reporting approach exists.

**Outcome**

The user receives a report over email while keeping WhatsApp interaction short.

## Story 7: Scheduling Recurring Reports

The user wants weekly discipline around spending:

> "Send me a weekly report every Monday morning showing my account balances and biggest expenses."

Mr Krabs creates a schedule with the report query, frequency, and next run time. If no time is supplied, the current implementation defaults the next scheduled run to the next day at 06:00 UTC. The scheduler later picks up due schedules, runs the saved query through the agent, emails the report, saves the report record, and advances the next run.

**Primary flow**

1. The agent calls `manage_schedule` with `action: create`.
2. The schedule is stored with query, frequency, next run, and enabled status.
3. The background scheduler checks for due schedules every five minutes.
4. When due, it runs the saved report query.
5. The scheduled report is emailed and saved with the schedule ID.
6. The schedule's next run is moved to the next daily or weekly 06:00 UTC slot.

**Current capabilities used**

- Create daily or weekly schedules.
- List schedules.
- Update schedule query, frequency, or next run.
- Enable or disable schedules.
- Delete schedules.
- Run due schedules automatically when the scheduler is enabled.

**Operational note**

The deployed container is expected to run as a single replica by default so due schedules are not processed twice.

## Story 8: Managing Existing Report Schedules

The user no longer wants a daily report and sends:

> "Disable my daily cashflow report."

Mr Krabs lists schedules if it needs to identify the correct one. It then disables the matching schedule without deleting it, so it can be enabled again later.

**Primary flow**

1. The agent calls `manage_schedule` with `action: list` if the schedule is ambiguous.
2. It calls `manage_schedule` with `action: disable` for the chosen schedule ID.
3. Mr Krabs confirms that the schedule is disabled.

**Supported schedule actions**

- `create`
- `list`
- `update`
- `enable`
- `disable`
- `delete`

## Story 9: Remembering Preferences

The user says:

> "When you report spending, separate groceries from restaurants."

Mr Krabs saves this as a preference. Later, when the user asks for spending reports, the agent searches memory at the start of the conversation and can apply that preference.

**Primary flow**

1. The agent recognizes the message as a lasting preference, habit, or fact.
2. It calls `save_memory`.
3. On later related requests, it calls `search_memory`.
4. The remembered preference influences the response or report structure.

**Current capabilities used**

- Save memories as preferences, habits, or facts.
- Search stored memories by keyword.
- Use remembered context across conversations.

## Story 10: Saving Reusable Analysis Skills

After refining a useful report format, the user wants Mr Krabs to reuse it:

> "Use this format for my monthly spending reviews from now on."

Mr Krabs can save a reusable skill with markdown instructions. Before future report or analysis work, it lists available skills and loads a matching one.

**Primary flow**

1. The agent calls `save_skill` with a short name, description, and markdown instructions.
2. On future report tasks, it calls `list_skills`.
3. If a relevant skill exists, it calls `load_skill`.
4. The loaded instructions guide the report structure.

**Current capabilities used**

- Save or update skills.
- List available skills.
- Load a named skill before related work.

## Story 11: Health and Operations

An operator wants to know whether the service is alive before wiring Twilio to it. They call:

```text
GET /ping
GET /health
```

`/ping` returns a lightweight status and UTC timestamp. `/health` runs dependency checks and returns HTTP 200 when healthy or HTTP 503 when unhealthy.

**Primary flow**

1. The operator calls `/ping` for a basic liveness check.
2. The operator calls `/health` for dependency status.
3. Deployment or monitoring can use the status code to detect whether the app is ready.

**Current capabilities used**

- Basic liveness endpoint.
- Dependency health endpoint.
- Legacy `/api/ping`, `/api/health`, and `/api/webhook` aliases for compatibility.

## Story 12: Local Agent Testing

A developer wants to test the assistant without sending real WhatsApp messages. They run:

```powershell
uv run python scripts\agent_chat.py
```

or:

```powershell
uv run python scripts\agent_chat.py "show my accounts"
```

The script loads the same environment, system prompt, model, and tool definitions used by the deployed app. This lets developers iterate on banking, reporting, memory, and scheduling behavior before exposing changes through the webhook.

## Cross-Cutting Rules

- WhatsApp replies should stay short and scannable.
- ZAR is the default currency unless account data says otherwise.
- Relative dates must be resolved before querying dated financial data.
- Raw API errors should be translated into plain language.
- Transfers and beneficiary payments require confirmation before execution.
- Reports should include clear totals, categories, and notable items.
- Langfuse tracing is used for agent and tool observations when configured.
- WhatsApp identifiers are hashed before being used as tracing session or user IDs.

## Current Boundaries

- The assistant is designed for a single user's Investec Private Banking context.
- Scheduled reports support daily and weekly frequencies.
- Scheduled report times are stored as concrete datetimes; default and recurring scheduler advancement currently use 06:00 UTC.
- The webhook expects Twilio form fields containing a WhatsApp sender and message body.
- Email reports are plain text.
- The application relies on configured Investec, OpenAI, Cosmos DB, Twilio, email, and optional Langfuse environment settings.
