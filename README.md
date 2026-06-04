# Mr Krabs

> Your personal Investec banking agent, accessible via WhatsApp.

Mr Krabs is an AI-powered assistant that lets you interact with your Investec accounts through WhatsApp. Send a message and Mr Krabs will check balances, review transactions, generate reports, and more in plain English.

---

## Features

### Banking
- Check account balances and account details
- View and filter transactions by date range, type, or pending status
- List beneficiaries and pay them
- Access documents and statements
- Transfer funds between accounts

### Reporting
- Receive reports by email via Azure Communication Services

### Memory
- Mr Krabs remembers your preferences, habits, and facts across conversations
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
                     reports)
                         |
                         v
              Azure Communication Services
                    (email reports)
```

The agent uses OpenAI's Responses API with a `ToolRegistry`. Banking tools live in `krabs_tools`, where Pydantic schemas define the model-facing contract and grouped factory functions compose account, document, and payment tools from an injected `BankingClient`. `InvestecClient` is the current provider implementation. Both the webhook runner and `scripts/agent_chat.py` use the same factory path so local testing and deployed behavior stay aligned.

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

With Docker Desktop running, start the local Azure Cosmos DB emulator container:

```powershell
docker compose up -d cosmos-db
```

The Cosmos DB endpoint runs at `http://localhost:8081`, the health probe at `http://localhost:8080/ready`, and Data Explorer at `http://localhost:1234`.

Initialize the local database and containers:

```powershell
uv run python scripts\init_local_cosmos.py
```

Run the API locally:

```powershell
uv run uvicorn krabs_application.fastapi_app:app --app-dir src --reload --port 8000
```

### Local agent chat

Use `scripts/agent_chat.py` to iterate on the agent directly without running the
FastAPI webhook. It loads `.env`, uses the same system prompt and tool
definitions as the app, and sends traces with the `local-agent-chat` session.

```powershell
uv run python scripts\agent_chat.py
uv run python scripts\agent_chat.py "show my accounts"
```

Or run the API in Docker for local development:

```powershell
docker compose up --build api
```

The API container reads `.env`, overrides Cosmos DB to use the Compose service address, and exposes the app at `http://localhost:8000`.

Useful endpoints:

- `GET /ping`
- `GET /health`
- `POST /webhook`
- `POST /api/webhook` legacy alias

---

## Deploy

Deploy infrastructure, populate Key Vault, build the image in ACR, and update the Container App:

```powershell
.\infrastructure\deploy.ps1 -ResourceGroup "rg-krabs" -Location "southafricanorth"
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
  krabs_application/       # FastAPI app, health, and agent routing
  krabs_agent/             # AI agent core, runner, and prompts
  krabs_domain/            # Domain models and data access
    models/                 # Pydantic data models
    repositories/           # Cosmos DB repositories
  krabs_services/          # External service integrations
    communication/          # Twilio (WhatsApp) + Azure email
    finance/                # Investec banking API client
  krabs_tools/             # Responses API tool registry, schemas, adapters, factories
infrastructure/             # Azure Bicep IaC templates
scripts/
  agent_chat.py             # Local CLI for chatting with the agent directly
  init_local_cosmos.py      # Initialize local Cosmos DB containers
tests/
  krabs_unit_tests/        # Unit tests (mocked dependencies)
  krabs_integration_tests/ # Integration tests (live Investec sandbox)
```
