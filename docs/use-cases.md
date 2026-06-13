# Mr Krabs Use Cases

Mr Krabs is a WhatsApp-first Investec banking assistant for one user. The user speaks in plain English, the assistant resolves the request, calls the relevant banking or reporting tools, and replies back through WhatsApp.

The stories below describe the current product behavior as implemented today.

See [use-case-diagrams.md](use-case-diagrams.md) for diagram views of these stories and their supporting systems.

## Cast

- **User**: The Investec account holder using WhatsApp.
- **Mr Krabs**: The AI banking assistant. It is concise, protective of the user's money, and uses a light Mr Krabs-style voice.
- **Investec API**: Source of account, balance, transaction, beneficiary, transfer, payment, and document data.
- **External Banks and Platforms**: Future sources of balances, transactions, savings accounts, investments, crypto holdings, loans, and bond data.
- **Cosmos DB**: Stores chat sessions and reports.
- **Twilio WhatsApp**: Receives user messages and delivers replies.
- **Azure Communication Services Email**: Configured for future report delivery.

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

## Story 6: Creating a Spending Scoreboard

The user wants a quick at-a-glance view of spending:

> "Show me my weekly spending scoreboard."

Mr Krabs resolves the requested period, gathers account and transaction data, and returns a compact scoreboard in WhatsApp. The scoreboard shows total spend, score, status, daily breakdown, top categories, largest expenses, and a short watch list.

**Primary flow**

1. The agent calls `resolve_date_range` for the requested period.
2. It calls account and transaction tools needed for the report.
3. It groups spend by day and obvious merchant/category patterns.
4. It calculates a simple score out of 100 based on spend level, concentration, fees, and unusually large items.
5. It replies with a short scoreboard in WhatsApp.

**Current capabilities used**

- Generate report content from banking data.
- Resolve reporting periods.
- Fetch accounts and transactions.
- Generate a WhatsApp-friendly scoreboard from banking data.

**Outcome**

The user can understand daily or weekly spending at a glance without opening the banking app.

## Story 7: Receiving a Daily Financial Scoreboard

Every morning, the user wants Mr Krabs to review yesterday's spending without being asked. The report should be easy to read at a glance in WhatsApp, so Mr Krabs generates a financial scoreboard image and sends it proactively.

The scoreboard highlights yesterday's total spend, score, status, top merchants, largest expenses, category warnings, unusual items, and a short recommendation for the day ahead.

**Primary flow**

1. A scheduled job runs once each morning in the user's local timezone.
2. The app resolves "yesterday" into concrete Johannesburg dates.
3. The agent fetches the relevant accounts and yesterday's transactions.
4. The report generator analyzes spend level, category patterns, large items, fees, subscriptions, and unusual behavior.
5. The app renders a compact financial scoreboard image.
6. The app sends a short WhatsApp message with the image attached.
7. The generated report and analysis summary are saved to the report store.

**Current and planned capabilities used**

- Resolve the daily reporting period.
- Fetch account and transaction data.
- Analyze yesterday's spend against budgets, goals, and recent behavior.
- Generate an image-based financial scoreboard for WhatsApp.
- Proactively send scheduled WhatsApp messages.
- Store generated reports for later review.

**Outcome**

The user receives a daily financial check-in that can be understood in seconds, without opening a spreadsheet or banking app.

**Guardrail**

The daily report may criticize spending and recommend corrective action, but it must not move money or make payments without explicit user confirmation.

## Story 8: Receiving a Weekly Financial Review by Email

At the end of each week, the user wants a deeper review of financial behavior. Mr Krabs generates a weekly report and emails it to the user using Azure Communication Services Email.

The weekly report summarizes total spend, income activity, category breakdowns, recurring payments, savings progress, goal progress, overspending risks, and suggested actions for the next week.

**Primary flow**

1. A scheduled job runs at the configured weekly review time.
2. The app resolves the weekly reporting period.
3. The agent fetches accounts, balances, and transactions for the period.
4. The report generator analyzes spending patterns, budget performance, cash flow, and progress toward goals.
5. The app generates a weekly report suitable for email delivery.
6. Azure Communication Services Email sends the report to the configured email address.
7. The generated report metadata and summary are saved to the report store.

**Current and planned capabilities used**

- Resolve weekly reporting periods.
- Fetch account, balance, and transaction data.
- Generate deeper weekly analysis from banking data.
- Email reports through Azure Communication Services Email.
- Store report history.

**Outcome**

The user receives a structured weekly financial review that supports planning, budgeting, and accountability beyond the short daily WhatsApp scoreboard.

**Guardrail**

Weekly reports should separate factual transaction analysis from financial advice. Recommendations should be practical and conservative unless the user has configured explicit goals and thresholds.

## Story 9: Tracking Monthly Net Worth

The user wants to become a millionaire and needs Mr Krabs to track whether their net worth is increasing throughout the year. Once a month, Mr Krabs calculates a net worth snapshot and compares it with previous months.

The net worth view should show total assets, total liabilities, net worth, month-on-month movement, year-to-date movement, and progress toward the user's millionaire goal.

**Primary flow**

1. A scheduled job runs at the configured monthly net worth review time.
2. The app fetches accounts, balances, and available liability data.
3. The report generator calculates assets, liabilities, and net worth.
4. The report generator compares the current snapshot with prior monthly snapshots.
5. Mr Krabs highlights whether net worth is moving up or down and explains the main drivers.
6. The app stores the monthly net worth snapshot for year-long trend tracking.
7. The report is included in the monthly or weekly review, depending on the user's configured preference.

**Current and planned capabilities used**

- Fetch account and balance data.
- Store monthly net worth snapshots.
- Track year-to-date net worth movement.
- Track progress toward a target net worth of at least R1,000,000.
- Explain changes in net worth using cash flow, debt, savings, and investment movement where data is available.

**Outcome**

The user can see whether their financial position is improving each month and how far they are from becoming a millionaire.

**Guardrail**

Net worth reporting should clearly separate known account balances from manually supplied or estimated assets and liabilities, such as property value, vehicle value, loans, or external investments.

## Story 10: Tracking Multiple Income Streams

The user wants to build wealth through multiple income streams. They currently have two income streams and expect a third income stream soon. Mr Krabs should track income sources separately so the user can see which streams are growing, which are inconsistent, and how total income supports savings, investing, and debt goals.

Income streams may include salary, business income, side projects, dividends, interest, rental income, refunds, or other recurring inflows.

**Primary flow**

1. The user defines or confirms known income streams.
2. The app classifies incoming transactions by source where possible.
3. The agent asks the user to label ambiguous income transactions.
4. The report generator summarizes income by stream for daily, weekly, monthly, and year-to-date views.
5. Mr Krabs compares income growth against spending growth, savings rate, and net worth progress.
6. The classified income history is stored for future analysis.

**Current and planned capabilities used**

- Detect and classify incoming transactions.
- Store user-confirmed income stream mappings.
- Track income by source over time.
- Compare income growth with spending, savings, debt, and net worth movement.
- Use income stream data in financial scoreboards and weekly reviews.

**Outcome**

The user can see whether their income base is becoming stronger and whether extra income is being converted into wealth instead of disappearing into lifestyle spend.

**Guardrail**

Income classification should be explainable and user-correctable. Ambiguous inflows should not be treated as recurring income until confirmed by the user or observed consistently over time.

## Story 11: Tracking External Banks, Investments, Crypto, and Debt

The user wants Mr Krabs to understand their full financial life across multiple institutions, not only Investec. They may open a savings account with another bank, buy stocks, buy bitcoin, hold investment portfolios, or take a bond with a different bank.

Mr Krabs should track these external assets and liabilities so reports, net worth snapshots, and goal planning reflect the user's real financial position.

**Primary flow**

1. The user adds an external financial profile, such as another bank account, investment account, crypto wallet, stock portfolio, savings account, loan, or bond.
2. The app records whether the profile is connected through an API, imported from a statement, or manually maintained.
3. The agent fetches, imports, or asks for updated balances depending on the profile type.
4. The report generator classifies each profile as an asset or liability.
5. Monthly net worth reports include the external profile with clear source and freshness metadata.
6. Mr Krabs highlights concentration risk, debt pressure, idle cash, and progress toward savings or investment goals where the data supports it.

**Current and planned capabilities used**

- Store external financial profiles.
- Track assets across banks, savings accounts, stock portfolios, crypto holdings, and investment platforms.
- Track liabilities such as bonds, loans, credit cards, overdrafts, and vehicle finance.
- Support manual balance updates where API access is unavailable.
- Include data freshness and source labels in reports.
- Roll external assets and liabilities into net worth tracking.

**Outcome**

The user gets one consolidated financial view across income, cash, investments, crypto, savings, property debt, and other obligations.

**Guardrail**

Mr Krabs may analyze the user's financial position and explain tradeoffs, but buying stocks, buying bitcoin, opening accounts, applying for a bond, or choosing financial products should be treated as user-directed actions. Product recommendations and investment advice should remain conservative, clearly caveated, and separate from factual tracking unless appropriate compliance support exists.

## Story 12: Health and Operations

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

## Story 13: Local Agent Testing

A developer wants to test the assistant without sending real WhatsApp messages. They run:

```powershell
uv run python scripts\agent_chat.py
```

or:

```powershell
uv run python scripts\agent_chat.py "show my accounts"
```

The script loads the same environment, system prompt, model, and Investec tool factory path used by the deployed app. This lets developers iterate on banking and reporting behavior before exposing changes through the webhook.

## Cross-Cutting Rules

- WhatsApp replies should stay short and scannable.
- ZAR is the default currency unless account data says otherwise.
- Relative dates must be resolved before querying dated financial data.
- Raw API errors should be translated into plain language.
- Transfers and beneficiary payments require confirmation before execution.
- Reports should include clear totals, categories, and notable items.
- Daily proactive reports should be rendered as image-based financial scoreboards for WhatsApp.
- Weekly proactive reports should be delivered by email.
- Monthly net worth tracking should show whether the user's financial position is improving over the year.
- Long-term goal tracking should support the user's target of reaching at least R1,000,000 net worth.
- Income streams should be tracked separately so the user can see how each stream contributes to savings, investing, and net worth growth.
- External banks, savings accounts, investments, crypto holdings, loans, and bonds should be represented as assets or liabilities with clear data source and freshness metadata.
- WhatsApp identifiers are hashed before being used as tracing session or user IDs.
- Investec tool adapters should be registered through grouped factory functions so the app runner and local agent chat stay consistent.

## Current Boundaries

- The assistant is currently designed for a single user's Investec Private Banking context.
- Future financial tracking may include external banks, savings accounts, investments, crypto holdings, bonds, loans, and manually supplied financial profiles.
- The webhook expects Twilio form fields containing a WhatsApp sender and message body.
- Manual spending scoreboards are returned over WhatsApp in v1.
- The application relies on configured Investec, OpenAI, Cosmos DB, Twilio, and email environment settings.
