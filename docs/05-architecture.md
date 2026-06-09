# 5. Architecture & Sequence Diagrams

Architecture style: **Clean Architecture + DDD**, with a clear dependency rule —
dependencies point **inward** (`domain` ← `application` ← `infrastructure`/`interface`).

---

## 5.1 C4 — System context

```mermaid
graph TB
    Owner["MSME Owner / Staff"]
    CA["CA / Vendor (Phase 2)"]

    subgraph KuberAIQ["KuberAIQ Platform"]
        Web["Web Dashboard (Next.js PWA)"]
        API["Backend API (FastAPI)"]
        AI["AI Copilot (LangGraph)"]
    end

    Entra["Microsoft Entra ID"]
    AOAI["Azure OpenAI (GPT-5)"]
    WA["WhatsApp Business Cloud API"]
    Blob["Azure Blob Storage"]
    PG[("Azure PostgreSQL")]

    Owner -->|HTTPS| Web
    Owner -->|Chat| WA
    Web -->|REST/JSON| API
    WA  -->|Webhook| API
    API --> AI
    AI  -->|LLM calls| AOAI
    API -->|OIDC validate| Entra
    Web -->|OIDC login| Entra
    API -->|send msg| WA
    API -->|PDF store/fetch| Blob
    API --> PG
    CA  -.->|GST export| Web
```

## 5.2 C4 — Containers

```mermaid
graph LR
    subgraph Client
        FE["Next.js Frontend\n(App Router, TS, Tailwind, shadcn)"]
    end
    subgraph Azure
        APPGW["App Gateway / Front Door\n(WAF, TLS)"]
        subgraph AppService["Azure App Service"]
            BE["FastAPI App\n(Uvicorn/Gunicorn)"]
            WK["Worker / Scheduler\n(overdue job, async sends)"]
        end
        KV["Key Vault"]
        PG[("PostgreSQL Flexible Server")]
        BLOB["Blob Storage"]
        AI["Azure OpenAI"]
        SPEECH["Azure Speech (voice)"]
        MON["App Insights / Monitor"]
    end
    WA["WhatsApp Cloud API"]
    ENTRA["Entra ID"]

    FE --> APPGW --> BE
    WA -->|webhook| APPGW
    BE --> PG
    BE --> BLOB
    BE --> AI
    BE --> SPEECH
    BE --> WA
    BE --> KV
    BE --> MON
    WK --> PG
    WK --> WA
    FE --> ENTRA
    BE --> ENTRA
```

## 5.3 Backend layered architecture (Clean Architecture)

```mermaid
graph TD
    subgraph Interface["Interface / API Layer"]
        R["FastAPI Routers\n(invoices, customers, collections, dashboard, ai, auth, webhooks)"]
        SCH["Pydantic Schemas\n(request/response DTOs)"]
        DEP["Dependencies\n(auth, db session, rate limit)"]
    end
    subgraph Application["Application Layer"]
        SVC["Services / Use Cases\n(InvoiceService, CollectionService, ...)"]
        UOW["Unit of Work"]
        PORTS["Ports (interfaces):\nRepositories, LLM, Storage, Notifier"]
    end
    subgraph Domain["Domain Layer (pure)"]
        ENT["Entities & Aggregates\n(Invoice, Customer, Payment)"]
        VO["Value Objects\n(Money, GSTIN, GstBreakup, Phone)"]
        DSVC["Domain Services\n(GstCalculator, InvoiceNumberPolicy)"]
        EVT["Domain Events"]
    end
    subgraph Infrastructure["Infrastructure Layer"]
        REPO["SQLAlchemy Repositories"]
        ORM["ORM Models / Mappers"]
        LLM["LangGraph / Azure OpenAI Adapter"]
        STORE["Blob Storage Adapter"]
        NOTIF["WhatsApp Adapter"]
        PDF["ReportLab PDF Generator"]
    end

    R --> SCH
    R --> DEP
    R --> SVC
    SVC --> PORTS
    SVC --> ENT
    SVC --> DSVC
    ENT --> VO
    DSVC --> VO
    REPO -.implements.-> PORTS
    LLM -.implements.-> PORTS
    STORE -.implements.-> PORTS
    NOTIF -.implements.-> PORTS
    REPO --> ORM
```

The **dependency rule**: `Domain` imports nothing outward. `Application` defines
**ports** (abstract interfaces); `Infrastructure` provides **adapters** that implement
them. Wiring happens via **dependency injection** in the composition root
(`app/api/deps.py` + `app/core/container.py`).

## 5.4 AI Copilot architecture (LangGraph)

```mermaid
graph TD
    IN["User message + context"] --> GUARD["Input Guardrail\n(sanitize, injection check)"]
    GUARD --> ROUTER["Router Node\n(intent classification)"]
    ROUTER -->|invoice| IA["Invoice Agent"]
    ROUTER -->|collections| CA["Collections Agent"]
    ROUTER -->|dashboard| DA["Dashboard Agent"]
    ROUTER -->|customer| CUA["Customer Agent"]
    ROUTER -->|unknown| FB["Fallback / Clarify"]

    IA --> TOOLS["Tool Executor\n(server-validated tools)"]
    CA --> TOOLS
    DA --> TOOLS
    CUA --> TOOLS

    TOOLS --> CONFIRM{"Write action?"}
    CONFIRM -->|yes| HUMAN["Return confirmation,\nawait user 'yes'"]
    CONFIRM -->|no| OUT
    HUMAN -->|confirmed| TOOLS
    TOOLS --> VALID["Output Guardrail\n(schema + GST validation)"]
    VALID --> OUT["Structured JSON response"]
```

## 5.5 Sequence — Create invoice via AI copilot

```mermaid
sequenceDiagram
    actor U as Owner
    participant FE as Frontend / WhatsApp
    participant API as FastAPI /ai/chat
    participant G as Guardrails
    participant LG as LangGraph Router
    participant IA as Invoice Agent
    participant SVC as InvoiceService
    participant GST as GstCalculator (domain)
    participant DB as PostgreSQL

    U->>FE: "Invoice ABC Traders, 50 bags cement @350, 18%"
    FE->>API: POST /ai/chat {message, session_id}
    API->>G: sanitize + injection check
    G-->>API: clean
    API->>LG: route(message, context)
    LG->>IA: intent=create_invoice, entities
    IA->>SVC: preview_invoice(customer, items)
    SVC->>GST: compute_gst(items, states)
    GST-->>SVC: breakup (CGST/SGST/IGST, totals)
    SVC-->>IA: draft summary (no commit)
    IA-->>API: confirmation payload
    API-->>FE: "Create this invoice? Total ₹20,650 ✅/❌"
    U->>FE: "Yes"
    FE->>API: POST /ai/chat {message:"yes", session_id}
    API->>LG: resume(session)
    LG->>IA: confirmed
    IA->>SVC: create_invoice(draft)
    SVC->>DB: INSERT invoice + items (tx)
    SVC->>DB: INSERT audit_log
    DB-->>SVC: invoice_id, number
    SVC-->>IA: invoice
    IA-->>API: result + pdf job
    API-->>FE: "Created INV/2025-26/0042. PDF ready."
```

## 5.6 Sequence — Bulk WhatsApp reminders (Collections)

```mermaid
sequenceDiagram
    actor U as Owner
    participant FE as Frontend
    participant API as FastAPI
    participant CS as CollectionService
    participant DB as PostgreSQL
    participant WA as WhatsApp Adapter
    participant WC as WhatsApp Cloud API

    U->>FE: "Send reminders to everyone overdue"
    FE->>API: POST /collections/reminders/bulk:preview
    API->>CS: find_overdue(company_id)
    CS->>DB: SELECT overdue invoices
    DB-->>CS: list (12 invoices, ₹2.3L)
    CS-->>API: preview {count:12, total:230000}
    API-->>FE: confirm 12 reminders, ₹2,30,000?
    U->>FE: Confirm
    FE->>API: POST /collections/reminders/bulk {idempotency_key}
    API->>CS: send_bulk(invoice_ids)
    loop each overdue invoice (cooldown respected)
        CS->>DB: check last reminder (cooldown)
        CS->>WA: send_template(phone, vars)
        WA->>WC: POST /messages
        WC-->>WA: message_id / error
        CS->>DB: INSERT reminder(status)
    end
    CS-->>API: summary {sent:11, skipped:1}
    API-->>FE: "Sent 11 reminders (1 skipped: cooldown)."
```

## 5.7 Sequence — OIDC login (Entra ID)

```mermaid
sequenceDiagram
    actor U as User
    participant FE as Next.js
    participant ENTRA as Entra ID
    participant API as FastAPI /auth

    U->>FE: Click "Sign in with Microsoft"
    FE->>ENTRA: Authorization request (PKCE)
    ENTRA-->>U: Login + consent
    U->>ENTRA: Credentials
    ENTRA-->>FE: auth code (redirect)
    FE->>API: POST /auth/callback {code, verifier}
    API->>ENTRA: Exchange code → id_token
    ENTRA-->>API: id_token (JWT)
    API->>API: Validate (iss, aud, sig, exp); upsert user
    API-->>FE: app access JWT (15m) + refresh (7d)
    FE->>FE: Store tokens (httpOnly cookie)
```

## 5.8 Deployment topology

```mermaid
graph TB
    subgraph Internet
        USER[Users]
        WAAPI[WhatsApp Cloud]
    end
    FD["Azure Front Door + WAF"]
    subgraph RG["Resource Group: rg-kuberaiq-prod (Central India)"]
        ASP["App Service Plan"]
        BE["App Service: api"]
        FE["App Service / Static Web App: web"]
        PG[("PostgreSQL Flexible Server\n+ read replica")]
        BLOB["Storage Account (Blob)"]
        KV["Key Vault"]
        AOAI["Azure OpenAI"]
        AI2["Application Insights"]
        LAW["Log Analytics"]
    end
    USER --> FD --> FE
    USER --> FD --> BE
    WAAPI --> FD --> BE
    BE --> PG
    BE --> BLOB
    BE --> KV
    BE --> AOAI
    BE --> AI2 --> LAW
    FE --> AI2
```
