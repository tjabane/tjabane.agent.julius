# Julius

<p align="center">
  <img src="https://static.tvmaze.com/uploads/images/medium_portrait/5/14972.jpg" alt="Julius" width="200"/>
</p>

> Your personal Investec banking agent, accessible via WhatsApp.

Julius is an AI-powered assistant that lets you interact with your Investec accounts through WhatsApp. Send a message and Julius will check balances, review transactions, schedule reports, and more — all in plain English.

---

## Features

### Banking
- Check account balances and account details
- View and filter transactions by date range, type, or pending status
- List beneficiaries and pay them
- Access documents and statements
- Transfer funds between accounts

### Reporting
- Schedule automated financial reports (daily or weekly)
- Receive reports by email via Azure Communication Services
- Manage schedules — create, update, enable, disable, or delete

### Memory
- Julius remembers your preferences, habits, and facts across conversations
- Save and recall custom query shortcuts (skills)

---

## How it works

```
You (WhatsApp)
     │
     ▼
Twilio  ──►  Azure Functions (webhook)
                    │
                    ▼
               OpenAI Agent
                    │
          ┌─────────┴──────────┐
          ▼                    ▼
   Investec API           Cosmos DB
   (banking data)   (sessions, memory,
                     schedules, reports)
                         │
                         ▼
              Azure Communication Services
                    (email reports)
```

A timer-triggered function runs every 5 minutes to dispatch any due scheduled reports.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Azure Functions (Python 3.12) |
| AI | OpenAI |
| Messaging | Twilio WhatsApp |
| Banking | Investec Private Banking API |
| Database | Azure Cosmos DB |
| Email | Azure Communication Services |
| Secrets | Azure Key Vault |
| IaC | Azure Bicep |

---

## Project Structure

```
src/
  julius_application/       # Agent logic and Azure Function triggers
    agent/                  # AI agent core, tools (banking, knowledge, reporting)
    functions/              # Function handlers (webhook, scheduler)
  julius_domain/            # Domain models and data access
    models/                 # Pydantic data models
    repositories/           # Cosmos DB repositories
  julius_services/          # External service integrations
    communication/          # Twilio (WhatsApp) + Azure email
    finance/                # Investec banking API client
infrastructure/             # Azure Bicep IaC templates
tests/
  julius_unit_tests/        # Unit tests (mocked dependencies)
  julius_integration_tests/ # Integration tests (live Investec sandbox)
```
