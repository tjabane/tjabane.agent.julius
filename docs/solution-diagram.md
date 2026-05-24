# Mr Krabs Solution Diagram

This diagram shows the deployed solution components and the main runtime paths for WhatsApp requests, banking/reporting tools, scheduled reports, and operational checks.

```mermaid
flowchart TB
    user[User<br/>WhatsApp]
    operator[Operator / Monitor]
    developer[Developer]

    subgraph external[External Services]
        twilio[Twilio WhatsApp]
        investec[Investec Private Banking API]
        openai[OpenAI]
        email[Azure Communication Services Email]
        langfuse[Langfuse<br/>optional tracing]
    end

    subgraph azure[Azure]
        subgraph containerApp[Azure Container Apps<br/>single replica by default]
            fastapi[FastAPI app]
            webhook[POST /webhook<br/>POST /api/webhook]
            health[GET /ping<br/>GET /health]
            agent[Mr Krabs agent runtime]
            scheduler[Background scheduler<br/>every 5 minutes]
            tools[Agent tools<br/>banking, dates, reporting, knowledge]
        end

        cosmos[(Azure Cosmos DB<br/>sessions, memories, skills,<br/>schedules, sent reports)]
        keyVault[Azure Key Vault<br/>configuration and secrets]
        acr[Azure Container Registry]
    end

    subgraph local[Local Development]
        cli[scripts/agent_chat.py]
        localApi[Local FastAPI / Docker run]
        localCosmos[Cosmos DB emulator]
    end

    developer --> cli
    developer --> localApi
    cli --> agent
    localApi --> fastapi
    localApi --> localCosmos

    user --> twilio
    twilio --> webhook
    webhook --> fastapi
    fastapi --> agent
    agent --> openai
    agent --> tools
    tools --> investec
    tools --> cosmos
    tools --> email
    agent -. traces .-> langfuse
    fastapi --> twilio
    twilio --> user

    scheduler --> agent
    scheduler --> cosmos
    scheduler --> email

    operator --> health
    health --> cosmos
    health --> investec
    health --> email

    keyVault --> fastapi
    acr --> containerApp
```

## Main Flows

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant Twilio as Twilio WhatsApp
    participant API as FastAPI webhook
    participant Agent as Mr Krabs agent
    participant OpenAI
    participant Tools as Agent tools
    participant Investec as Investec API
    participant Cosmos as Cosmos DB
    participant Email as ACS Email

    User->>Twilio: Send WhatsApp message
    Twilio->>API: POST /webhook
    API->>Cosmos: Load chat session
    API->>Agent: Run message with context
    Agent->>OpenAI: Reason over request
    Agent->>Tools: Call required tool
    alt Banking data needed
        Tools->>Investec: Accounts, balances, transactions, documents, payments, transfers
        Investec-->>Tools: Banking response
    end
    alt Memory, skills, schedules, or report records needed
        Tools->>Cosmos: Read or write stored state
        Cosmos-->>Tools: Stored data
    end
    alt Email report requested
        Tools->>Email: Send plain-text report
        Email-->>Tools: Delivery result
    end
    Tools-->>Agent: Tool result
    Agent-->>API: Final WhatsApp response
    API->>Cosmos: Save updated session
    API-->>Twilio: Reply message
    Twilio-->>User: Deliver response
```

## Scheduled Report Flow

```mermaid
sequenceDiagram
    autonumber
    participant Scheduler
    participant Cosmos as Cosmos DB
    participant Agent as Mr Krabs agent
    participant Investec as Investec API
    participant Email as ACS Email

    Scheduler->>Cosmos: Find due enabled schedules
    loop For each due schedule
        Scheduler->>Agent: Run saved report query
        Agent->>Investec: Fetch accounts and transactions
        Investec-->>Agent: Banking data
        Agent->>Email: Send report
        Email-->>Agent: Delivery result
        Agent->>Cosmos: Save sent report record
        Scheduler->>Cosmos: Advance next run
    end
```
