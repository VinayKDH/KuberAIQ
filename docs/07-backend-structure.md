# 7. Backend Folder Structure

FastAPI + Clean Architecture + DDD. The **dependency rule** is enforced by package
boundaries: `domain` imports nothing from `application`/`infrastructure`/`api`.

```
backend/
├── pyproject.toml                # deps, ruff/black/mypy/pytest config
├── alembic.ini
├── Dockerfile
├── .env.example
├── gunicorn_conf.py
├── alembic/
│   ├── env.py
│   └── versions/                 # migration scripts
└── app/
    ├── main.py                   # FastAPI app factory, middleware, router mount
    │
    ├── core/                     # cross-cutting (framework-agnostic config)
    │   ├── config.py             # pydantic-settings (12-factor env)
    │   ├── constants.py          # ALL static values live here (per user rule)
    │   ├── logging.py            # structured JSON logging setup
    │   ├── security.py           # JWT encode/decode, password/none, hashing
    │   ├── errors.py             # domain/app exception types + handlers
    │   └── container.py          # DI composition root (wires ports→adapters)
    │
    ├── domain/                   # PURE business model (no FastAPI/SQLAlchemy)
    │   ├── entities/
    │   │   ├── invoice.py        # Invoice aggregate + InvoiceItem entity
    │   │   ├── customer.py
    │   │   ├── payment.py
    │   │   ├── reminder.py
    │   │   ├── company.py
    │   │   └── user.py
    │   ├── value_objects/
    │   │   ├── money.py          # Money (Decimal, currency)
    │   │   ├── gstin.py          # GSTIN VO with checksum validation
    │   │   ├── phone.py          # Indian phone VO
    │   │   └── gst_breakup.py    # CGST/SGST/IGST split
    │   ├── enums.py              # InvoiceStatus, UserRole, ... (mirror DB enums)
    │   ├── services/             # domain services (stateless business rules)
    │   │   ├── gst_calculator.py # deterministic GST math
    │   │   └── invoice_numbering.py
    │   ├── events.py             # domain events (InvoiceIssued, ReminderSent)
    │   └── exceptions.py         # domain errors (InvalidGstin, InvoiceNotEditable)
    │
    ├── application/              # use cases + ports (interfaces)
    │   ├── ports/                # abstract interfaces (DIP)
    │   │   ├── repositories.py   # CustomerRepo, InvoiceRepo, ... Protocols
    │   │   ├── unit_of_work.py   # UnitOfWork Protocol
    │   │   ├── llm.py            # LlmPort
    │   │   ├── storage.py        # StoragePort (blob)
    │   │   ├── notifier.py       # NotifierPort (whatsapp/sms/email)
    │   │   └── pdf.py            # PdfGeneratorPort
    │   ├── dto/                  # input/output dataclasses for use cases
    │   └── services/            # use-case orchestration (the "Service Layer")
    │       ├── customer_service.py
    │       ├── invoice_service.py
    │       ├── payment_service.py
    │       ├── collection_service.py
    │       ├── dashboard_service.py
    │       └── ai_service.py     # bridges API ↔ LangGraph agents
    │
    ├── infrastructure/           # adapters implementing application ports
    │   ├── db/
    │   │   ├── base.py           # declarative base, naming conventions
    │   │   ├── session.py        # async engine/sessionmaker
    │   │   ├── models/           # SQLAlchemy ORM models (mirror schema)
    │   │   │   ├── invoice.py
    │   │   │   ├── customer.py
    │   │   │   └── ...
    │   │   ├── mappers/          # ORM ↔ domain entity mapping
    │   │   ├── repositories/     # concrete repos (implement ports)
    │   │   │   ├── invoice_repository.py
    │   │   │   ├── customer_repository.py
    │   │   │   └── ...
    │   │   └── unit_of_work.py   # SQLAlchemy UoW
    │   ├── ai/
    │   │   ├── azure_openai_client.py
    │   │   ├── mock_llm.py        # deterministic stub (USE_MOCK_LLM)
    │   │   ├── graph/             # LangGraph definitions
    │   │   │   ├── state.py
    │   │   │   ├── router.py
    │   │   │   ├── build.py       # assembles the compiled graph
    │   │   │   └── agents/
    │   │   │       ├── invoice_agent.py
    │   │   │       ├── collections_agent.py
    │   │   │       ├── dashboard_agent.py
    │   │   │       └── customer_agent.py
    │   │   ├── tools/             # typed tool definitions + executor
    │   │   ├── prompts/           # system/tool prompts (versioned)
    │   │   └── guardrails.py      # injection filter, output validation
    │   ├── storage/
    │   │   ├── azure_blob.py
    │   │   └── local_blob.py      # USE_MOCK_BLOB
    │   ├── notifications/
    │   │   ├── whatsapp_client.py
    │   │   └── mock_notifier.py   # USE_MOCK_WHATSAPP
    │   ├── pdf/
    │   │   └── reportlab_generator.py
    │   └── auth/
    │       ├── entra.py           # OIDC token validation
    │       └── mock_auth.py       # USE_MOCK_AUTH
    │
    ├── api/                       # interface layer (HTTP)
    │   ├── deps.py                # FastAPI dependencies (auth, db, services, rbac)
    │   ├── middleware.py          # request-id, logging, rate limit, security headers
    │   ├── schemas/               # Pydantic request/response models
    │   │   ├── invoice.py
    │   │   ├── customer.py
    │   │   ├── payment.py
    │   │   ├── collection.py
    │   │   ├── dashboard.py
    │   │   ├── ai.py
    │   │   └── common.py          # pagination, error envelope
    │   └── v1/
    │       ├── router.py          # aggregates all v1 routers
    │       └── routes/
    │           ├── auth.py
    │           ├── customers.py
    │           ├── invoices.py
    │           ├── payments.py
    │           ├── collections.py
    │           ├── dashboard.py
    │           ├── ai.py
    │           └── webhooks.py    # WhatsApp inbound + status
    │
    ├── workers/
    │   ├── scheduler.py           # APScheduler: mark overdue, retries
    │   └── jobs.py
    │
    └── tests/
        ├── conftest.py
        ├── unit/                  # domain + services (mocked ports)
        ├── integration/           # repos against test Postgres
        ├── api/                   # FastAPI TestClient
        ├── agents/                # LangGraph agent + tool tests
        └── e2e/                   # full-flow smoke tests
```

## Layering rules (enforced)

| Layer | May import | Must NOT import |
| --- | --- | --- |
| `domain` | stdlib, `pydantic`-free pure python | FastAPI, SQLAlchemy, LangGraph, `application`, `infrastructure` |
| `application` | `domain`, `ports` | FastAPI, SQLAlchemy, concrete adapters |
| `infrastructure` | `domain`, `application.ports`, frameworks | `api` |
| `api` | `application`, `core`, schemas | direct `infrastructure` (only via DI container) |

DI wiring: `core/container.py` builds adapter instances; `api/deps.py` exposes them to
routers via FastAPI `Depends`. Swapping real ↔ mock adapters is a config flag, no code change.
