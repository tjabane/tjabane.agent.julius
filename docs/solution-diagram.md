# Mr Krabs Solution Diagram

This diagram shows the deployed solution components and the main runtime paths for WhatsApp requests, banking/reporting tools, and operational checks.

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
    end

    subgraph azure[Azure]
        subgraph containerApp[Azure Container Apps<br/>single replica by default]
            fastapi[FastAPI app]
            webhook[POST /webhook<br/>POST /api/webhook]
            health[GET /ping<br/>GET /health]
            agent[Mr Krabs agent runtime]
            registry[Tool registry<br/>Responses API functions]
            tools[Tool adapters<br/>Investec, dates, reporting, knowledge]
        end

        cosmos[(Azure Cosmos DB<br/>sessions, memories, skills,<br/>sent reports)]
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
    agent --> registry
    registry --> tools
    tools --> investec
    tools --> cosmos
    tools --> email
    fastapi --> twilio
    twilio --> user

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
    participant Tools as Tool registry/adapters
    participant Investec as Investec API
    participant Cosmos as Cosmos DB
    participant Email as ACS Email

    User->>Twilio: Send WhatsApp message
    Twilio->>API: POST /webhook
    API->>Cosmos: Load chat session
    API->>Agent: Run message with context
    Agent->>OpenAI: Reason over request with registered tools
    OpenAI-->>Agent: Function call request when data/action is needed
    Agent->>Tools: Validate arguments and call required tool
    alt Banking data needed
        Tools->>Investec: Accounts, balances, transactions, documents, payments, transfers
        Investec-->>Tools: Banking response
    end
    alt Memory, skills, or report records needed
        Tools->>Cosmos: Read or write stored state
        Cosmos-->>Tools: Stored data
    end
    alt Email report requested
        Tools->>Email: Send plain-text report
        Email-->>Tools: Delivery result
    end
    Tools-->>Agent: Tool result
    Agent->>OpenAI: Continue response with tool output
    Agent-->>API: Final WhatsApp response
    API->>Cosmos: Save updated session
    API-->>Twilio: Reply message
    Twilio-->>User: Deliver response
```

## Tool Composition

Investec tools are composed explicitly at the application boundary:

1. `InvestecClient` owns the HTTP-backed account, document, and payment clients.
2. `krabs_tools.tools.factories` groups concrete tool adapters by dependency: `create_investec_account_tools`, `create_investec_document_tools`, and `create_investec_payment_tools`.
3. `create_investec_tools` combines those groups for the normal app path.
4. `ToolRegistry.register_many` registers the resulting tools for the Responses API.
5. `krabs_agent.agent_runner` and `scripts/agent_chat.py` both use the same factory path.

This keeps external dependencies visible while avoiding one-by-one registration in every entry point.
