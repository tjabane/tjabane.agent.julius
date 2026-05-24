# Mr Krabs Use Case Diagrams

These diagrams summarize the use cases described in [use-cases.md](use-cases.md).

For the solution-level architecture view, see [solution-diagram.md](solution-diagram.md).

## System Context

```mermaid
flowchart LR
    user[User<br/>Investec account holder]
    operator[Operator]
    developer[Developer]

    subgraph system[Mr Krabs WhatsApp Banking Assistant]
        webhook((WhatsApp webhook))
        agent((AI banking assistant))
        scheduler((Report scheduler))
        health((Health endpoints))
        cli((Local agent chat))
    end

    twilio[Twilio WhatsApp]
    investec[Investec API]
    cosmos[Cosmos DB]
    email[Azure Communication Services Email]
    langfuse[Langfuse tracing]

    user --> twilio
    twilio --> webhook
    webhook --> agent
    agent --> investec
    agent --> cosmos
    agent --> email
    agent -. optional tracing .-> langfuse

    scheduler --> agent
    scheduler --> cosmos
    scheduler --> email

    operator --> health
    health --> cosmos
    developer --> cli
    cli --> agent
```

## User Banking Requests

```mermaid
flowchart LR
    user[User]

    subgraph assistant[Mr Krabs]
        balance((Check available money))
        transactions((Review recent spending))
        pay((Pay saved beneficiary))
        transfer((Move money between own accounts))
        documents((Get statements or tax certificates))
        confirmPay{{Confirm payment}}
        confirmTransfer{{Confirm transfer}}
        resolveDates((Resolve relative dates))
        resolveAccounts((Resolve account))
        summarize((Send concise WhatsApp reply))
    end

    investec[Investec API]
    twilio[Twilio WhatsApp]

    user --> balance
    user --> transactions
    user --> pay
    user --> transfer
    user --> documents

    balance --> resolveAccounts
    transactions --> resolveDates
    transactions --> resolveAccounts
    pay --> resolveAccounts
    pay --> confirmPay
    transfer --> resolveAccounts
    transfer --> confirmTransfer
    documents --> resolveDates
    documents --> resolveAccounts

    resolveAccounts --> investec
    resolveDates --> investec
    balance --> investec
    transactions --> investec
    confirmPay --> investec
    confirmTransfer --> investec
    documents --> investec

    investec --> summarize
    summarize --> twilio
    twilio --> user
```

## Reports and Scheduling

```mermaid
flowchart LR
    user[User]
    schedulerActor[Scheduler]

    subgraph assistant[Mr Krabs]
        onceOffReport((Create once-off financial report))
        createSchedule((Schedule recurring report))
        manageSchedule((Manage existing schedules))
        runDue((Run due scheduled report))
        resolveDates((Resolve reporting period))
        gatherData((Gather accounts and transactions))
        draftReport((Draft report))
        emailReport((Email report))
        saveRecord((Save report record))
        advanceSchedule((Advance next run))
    end

    investec[Investec API]
    cosmos[Cosmos DB]
    email[Azure Communication Services Email]

    user --> onceOffReport
    user --> createSchedule
    user --> manageSchedule
    schedulerActor --> runDue

    onceOffReport --> resolveDates
    onceOffReport --> gatherData
    gatherData --> investec
    gatherData --> draftReport
    draftReport --> emailReport
    emailReport --> email
    draftReport --> saveRecord
    saveRecord --> cosmos

    createSchedule --> cosmos
    manageSchedule --> cosmos

    runDue --> cosmos
    runDue --> gatherData
    runDue --> emailReport
    runDue --> saveRecord
    runDue --> advanceSchedule
    advanceSchedule --> cosmos
```

## Memory and Reusable Skills

```mermaid
flowchart LR
    user[User]

    subgraph assistant[Mr Krabs]
        remember((Remember preference))
        searchMemory((Search remembered context))
        saveSkill((Save reusable analysis skill))
        listSkills((List available skills))
        loadSkill((Load matching skill))
        applyContext((Apply context to answer or report))
    end

    cosmos[Cosmos DB]

    user --> remember
    user --> saveSkill
    user --> applyContext

    remember --> cosmos
    saveSkill --> cosmos

    applyContext --> searchMemory
    applyContext --> listSkills
    listSkills --> loadSkill
    searchMemory --> cosmos
    listSkills --> cosmos
    loadSkill --> cosmos
```

## Operations and Local Testing

```mermaid
flowchart LR
    operator[Operator]
    developer[Developer]

    subgraph app[Mr Krabs Application]
        ping((GET /ping))
        health((GET /health))
        apiAliases((Legacy /api aliases))
        cli((scripts/agent_chat.py))
        agent((Agent runtime))
    end

    cosmos[Cosmos DB]
    investec[Investec API]
    email[Email provider]
    twilio[Twilio provider]
    langfuse[Langfuse]

    operator --> ping
    operator --> health
    operator --> apiAliases
    health --> cosmos
    health --> investec
    health --> email
    health --> twilio

    developer --> cli
    cli --> agent
    agent --> investec
    agent --> cosmos
    agent -. optional tracing .-> langfuse
```

## Cross-Cutting Constraints

```mermaid
flowchart TD
    request[Incoming request]
    dates{Uses dated financial data?}
    money{Moves money?}
    report{Creates report?}
    trace{Tracing configured?}
    reply[Plain-language short reply]

    request --> dates
    dates -- yes --> resolve[Resolve relative dates first]
    dates -- no --> money
    resolve --> money

    money -- yes --> confirm[Require explicit confirmation]
    money -- no --> report
    confirm --> execute[Execute after confirmation only]
    execute --> report

    report -- yes --> totals[Include totals, categories, notable items]
    report -- no --> errors
    totals --> errors[Translate raw API errors]

    errors --> trace
    trace -- yes --> hash[Hash WhatsApp identifiers]
    trace -- no --> reply
    hash --> reply
```
