# Julius

<p align="center">
  <img src="https://static.tvmaze.com/uploads/images/medium_portrait/5/14972.jpg" alt="Julius" width="200"/>
</p>

> Your personal Investec banking agent, accessible via WhatsApp.

Julius is an AI-powered assistant that lets you interact with your Investec accounts through WhatsApp. Send a message and Julius will check balances, review transactions, schedule reports, and more in plain English.

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
- Manage schedules: create, update, enable, disable, or delete

### Memory
- Julius remembers your preferences, habits, and facts across conversations
- Save and recall custom query shortcuts (skills)

---

## How it works

```
You (WhatsApp)
     |
     v
Twilio  --->  Azure Container Apps (FastAPI webhook)
                    |
                    v
               OpenAI Agent
                    |
          +---------+---------+
          v                   v
   Investec API           Cosmos DB
   (banking data)   (sessions, memory,
                     schedules, reports)
                         |
                         v
              Azure Communication Services
                    (email reports)
```

The FastAPI process runs a background scheduler every 5 minutes to dispatch due scheduled reports. The Container App is configured with one replica by default so scheduled reports are not processed twice.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | FastAPI on Azure Container Apps |
| Container Registry | Azure Container Registry |
| AI | OpenAI |
| Messaging | Twilio WhatsApp |
| Banking | Investec Private Banking API |
| Database | Azure Cosmos DB |
| Email | Azure Communication Services |
| Secrets | Azure Key Vault |
| IaC | Azure Bicep |

---

## Local Development

Install dependencies:

```powershell
uv sync
```

Run the API locally:

```powershell
$env:SCHEDULER_ENABLED = "false"
uv run uvicorn julius_application.api:app --app-dir src --reload --port 8000
```

Useful endpoints:

- `GET /ping`
- `GET /health`
- `POST /webhook`
- `POST /api/webhook` legacy alias

---

## Deploy

Deploy infrastructure, populate Key Vault, build the image in ACR, and update the Container App:

```powershell
.\infrastructure\deploy.ps1 -ResourceGroup "rg-julius" -Location "southafricanorth"
```

After deployment, configure Twilio WhatsApp to call:

```text
https://<container-app-fqdn>/webhook
```

The legacy alias remains available at:

```text
https://<container-app-fqdn>/api/webhook
```

---

## Project Structure

```
src/
  julius_application/       # FastAPI app, scheduler, health, and agent logic
    agent/                  # AI agent core, tools (banking, knowledge, reporting)
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
