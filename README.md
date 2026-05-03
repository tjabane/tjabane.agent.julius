# Julius — Personal Banking Agent

Julius is a personal Investec Private Banking agent accessible over WhatsApp. It answers balance queries, executes transfers, schedules recurring reports, and builds a persistent memory of the user's preferences — all through natural conversation.

## Architecture overview

```
WhatsApp → Twilio → Azure Functions (webhook) → OpenAI GPT-4o → Investec API
                                                      ↑
                                              Azure CosmosDB
                                        (sessions, schedules, memory)
                                                      ↓
                                       Azure Communication Services (email)
```

Two Azure Functions handle all traffic:

| Function | Trigger | Purpose |
|---|---|---|
| `webhook` | HTTP POST `/webhook` | Receives Twilio WhatsApp messages and returns a reply |
| `scheduler` | Timer (every 5 min) | Fires due scheduled reports and advances their next-run time |

The agent uses OpenAI's tool-calling interface. Each user turn enters a loop: the model either returns a final reply or requests tool calls, which are executed and fed back until the model stops.

## Project structure

```
.
├── function_app.py          # Azure Functions v2 entry point
├── agent/
│   ├── agent.py             # run() and run_scheduled() — the agent loop
│   ├── prompts/
│   │   └── system.md        # System prompt served to GPT-4o
│   └── tools/
│       ├── __init__.py      # ALL_DEFINITIONS aggregator + dispatch()
│       ├── deps.py          # ToolDeps — injectable service container
│       ├── banking/         # get_accounts, get_balance, get_transactions,
│       │                    #   transfer_funds, get_beneficiaries,
│       │                    #   pay_beneficiary, get_documents
│       ├── knowledge/       # save_memory, search_memory,
│       │                    #   save_skill, load_skill, list_skills
│       └── reporting/       # manage_schedule, send_email
├── models/
│   ├── agent.py             # Session, Message
│   ├── reporting.py         # Schedule, Frequency, Report
│   └── knowledge.py         # Memory, MemoryType, Skill
├── repositories/
│   ├── agent.py             # SessionRepository
│   ├── reporting.py         # ScheduleRepository, ReportRepository
│   └── knowledge.py         # MemoryRepository, SkillRepository
├── services/
│   ├── investec_client.py   # Investec Private Banking API wrapper
│   ├── email_service.py     # Azure Communication Services email
│   └── twilio_client.py     # Twilio WhatsApp send + webhook parse
└── tests/
    ├── conftest.py           # dummy_env autouse fixture
    └── agent/
        ├── test_agent.py
        ├── test_tools_banking.py
        ├── test_tools_reporting.py
        └── test_tools_knowledge.py
```

## Local setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- An Investec sandbox or live API key

### Install dependencies

```bash
uv sync
```

### Environment variables

Create a `.env` file at the project root:

```env
# Investec
INVESTEC_CLIENT_ID=
INVESTEC_CLIENT_SECRET=
INVESTEC_API_KEY=
INVESTEC_SANDBOX=true          # set to false for live accounts

# OpenAI
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o            # optional, defaults to gpt-4o

# Azure CosmosDB
COSMOS_CONNECTION_STRING=
COSMOS_DATABASE=julius

# Twilio (WhatsApp)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=        # e.g. +14155238886

# Azure Communication Services (email)
AZURE_COMMUNICATION_CONNECTION_STRING=
EMAIL_SENDER_ADDRESS=
EMAIL_RECIPIENT_ADDRESS=
```

### Run tests

```bash
# Unit tests only (no credentials required)
uv run pytest tests/ -m "not integration" -v

# Integration tests (requires real .env credentials)
uv run pytest tests/ -m integration -v
```

## Tool reference

### Banking (`agent/tools/banking/`)

| Tool | Description |
|---|---|
| `get_accounts` | List all accounts with IDs and product types |
| `get_balance` | Current, available, and cash balance for an account |
| `get_transactions` | Transaction history with optional date range and type filter |
| `transfer_funds` | Transfer to one or more Investec accounts |
| `get_beneficiaries` | List saved beneficiaries and categories |
| `pay_beneficiary` | Pay one or more beneficiaries |
| `get_documents` | List or retrieve statements and tax certificates |

### Knowledge (`agent/tools/knowledge/`)

| Tool | Description |
|---|---|
| `save_memory` | Persist a user preference, habit, or fact |
| `search_memory` | Keyword search over stored memories |
| `save_skill` | Save markdown instructions for a recurring task type |
| `load_skill` | Load a skill by name to guide the current task |
| `list_skills` | List all saved skills |

### Reporting (`agent/tools/reporting/`)

| Tool | Description |
|---|---|
| `manage_schedule` | Create, update, enable, disable, delete, or list schedules |
| `send_email` | Send a financial report via email and save it to CosmosDB |

## Dependency injection

All tools accept an optional `ToolDeps` parameter for unit testing. In production, singletons are lazily initialised on first invocation so Azure Functions can register functions before Key Vault references resolve.

```python
@dataclass
class ToolDeps:
    investec: InvestecClient | None = None
    schedule_repo: ScheduleRepository | None = None
    report_repo: ReportRepository | None = None
    email: EmailService | None = None
    memory_repo: MemoryRepository | None = None
    skill_repo: SkillRepository | None = None
```

Pass a `ToolDeps` instance with stubs to `run()` or `run_scheduled()` in tests — no `monkeypatch` needed.

## CosmosDB schema

All collections live in the `julius` database.

| Collection | Model | Key fields |
|---|---|---|
| `sessions` | `Session` | `id` (WhatsApp number), `messages[]` |
| `schedules` | `Schedule` | `id`, `query`, `frequency`, `next_run`, `enabled` |
| `reports` | `Report` | `id`, `query`, `content`, `schedule_id`, `created_at` |
| `memories` | `Memory` | `id`, `type` (preference/habit/fact), `content` |
| `skills` | `Skill` | `id`, `name`, `description`, `content` |

## CI/CD pipeline

Defined in `.github/workflows/ci-cd.yml`. Three jobs run in sequence on every push to `master`:

```
test → deploy-dev → deploy-prod
```

| Job | Environment | Gate |
|---|---|---|
| `test` | — | Unit tests must pass |
| `deploy-dev` | `dev` | Runs automatically after tests pass |
| `deploy-prod` | `prod` | Requires manual approval in GitHub |

### Secrets required

| Secret | Where |
|---|---|
| `AZURE_CREDENTIALS` | Repository secret — service principal JSON from `az ad sp create-for-rbac` |

### Environment variables

| Variable | Environment | Value |
|---|---|---|
| `FUNCTION_APP_NAME` | `prod` | Name of the production Function App |

The pipeline exports `requirements.txt` at deploy time using `uv export --no-dev --no-hashes` and strips the editable install line (`-e .`) so the Azure remote Oryx build succeeds.

## Deployment (manual)

```bash
# Export dependencies
uv export --no-dev --no-hashes -o requirements.txt
# Remove editable install line if present
sed -i '/^-e /d' requirements.txt

# Deploy via Azure CLI
az login
func azure functionapp publish <FUNCTION_APP_NAME> --python --build remote
```

### Azure app settings

All secrets are stored in Azure Key Vault and referenced via Key Vault references. Set them with:

```bash
az functionapp config appsettings set \
  --name <FUNCTION_APP_NAME> \
  --resource-group <RESOURCE_GROUP> \
  --% --settings "OPENAI_API_KEY=@Microsoft.KeyVault(VaultName=<VAULT>;SecretName=openai-api-key)"
```

Note: use the `--% ` stop-parsing token in PowerShell to prevent semicolons in Key Vault references from being interpreted as statement separators.

## Twilio webhook configuration

Set the Twilio sandbox (or production) WhatsApp webhook URL to:

```
https://<FUNCTION_APP_NAME>.azurewebsites.net/api/webhook?code=<FUNCTION_KEY>
```

The function key is available in the Azure Portal under **Functions → webhook → Function Keys**.
