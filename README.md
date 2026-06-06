# VyaparAI

> **AI Business Manager for Indian MSMEs**

VyaparAI is a production-grade SaaS platform that gives Indian MSME (Micro, Small & Medium Enterprise) owners an AI-powered business copilot. Owners run their day-to-day operations — invoicing, collections, GST, cash flow, customers — through **natural language** over **WhatsApp**, a **web dashboard**, and **voice**.

```
"Create invoice for ABC Traders for 50 bags cement."
"Who has not paid me?"
"Generate GST report."
"What is my expected cash flow next month?"
```

---

## Monorepo layout

```
VyaparAI/
├── docs/                # Deliverables 1–15: PRD, requirements, architecture, schema, specs, roadmap
├── backend/             # FastAPI service (Clean Architecture + DDD)
├── frontend/            # Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui
├── infra/               # IaC (Bicep), monitoring, backup strategy
├── .github/workflows/   # CI/CD (GitHub Actions → Azure)
├── docker-compose.yml   # Local dev: Postgres + backend + frontend
└── README.md
```

## Tech stack

| Layer          | Technology                                              |
| -------------- | ------------------------------------------------------- |
| Frontend       | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui         |
| Backend        | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic           |
| Database       | PostgreSQL 16                                            |
| AI             | Azure OpenAI (GPT-5), LangGraph                          |
| Storage        | Azure Blob Storage                                       |
| Auth           | Microsoft Entra ID (OIDC) + JWT                          |
| Notifications  | WhatsApp Business Cloud API                              |
| PDF            | ReportLab                                                |
| Deployment     | Azure App Service, Azure Database for PostgreSQL, Blob  |

## Architecture principles

Clean Architecture · Domain-Driven Design · SOLID · Repository Pattern · Service Layer · Dependency Injection.

## Documentation index (deliverables)

| #  | Document |
| -- | -------- |
| 1  | [Product Requirements Document](docs/01-product-requirements.md) |
| 2  | [User Stories](docs/02-user-stories.md) |
| 3  | [Functional Requirements](docs/03-functional-requirements.md) |
| 4  | [Non-Functional Requirements](docs/04-non-functional-requirements.md) |
| 5  | [Architecture & Sequence Diagrams](docs/05-architecture.md) |
| 6  | [Database Schema & ER Diagram](docs/06-database-schema.md) |
| 7  | [Backend Folder Structure](docs/07-backend-structure.md) |
| 8  | [Frontend Folder Structure](docs/08-frontend-structure.md) |
| 9  | [API Specifications](docs/09-api-specifications.md) |
| 10 | [LangGraph Agent Design & Prompt Engineering](docs/10-langgraph-agent-design.md) |
| 11 | [Azure Architecture](docs/11-azure-architecture.md) |
| 12 | [Security Design](docs/12-security-design.md) |
| 13 | [UI Wireframes](docs/13-ui-wireframes.md) |
| 14 | [Development Roadmap](docs/14-development-roadmap.md) |
| 15 | [Sprint Plan](docs/15-sprint-plan.md) |

## Quick start (local)

**Prerequisites:** Python 3.12, Node 18+, PostgreSQL 16 (or Docker Desktop for the full stack).

### Option A — Native (fastest for daily dev)

```bash
# 1. Database (one-time)
psql -U postgres -c "CREATE USER vyaparai WITH PASSWORD 'vyaparai';" 2>/dev/null || true
psql -U postgres -c "CREATE DATABASE vyaparai OWNER vyaparai;" 2>/dev/null || true

# 2. Env + migrations
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
cd backend && pip install -e ".[dev]" && alembic upgrade head

# 3. Start services (two terminals)
uvicorn app.main:app --reload --port 8000          # backend
cd ../frontend && npm install && npm run dev       # frontend

# 4. Smoke test
../scripts/smoke_test.sh
```

| Service | URL |
| --- | --- |
| Frontend | http://localhost:3000 |
| Backend / Swagger | http://localhost:8000/docs |
| Demo login email | `owner@demo.vyaparai.com` |

### Option B — Docker Compose

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
docker compose up --build
```

Backend → http://localhost:8000 · Frontend → http://localhost:3000 · Postgres → `localhost:5432` (user/pass/db: `vyaparai`)

External services (Azure OpenAI, Blob, WhatsApp, Entra ID) are **mocked by default** so the
platform runs locally with zero cloud credentials. Flip the toggles in `.env` to use the real
services. See [docs/04-non-functional-requirements.md](docs/04-non-functional-requirements.md)
and `backend/.env.example` for the full list of toggles.

### DevOps & infra

| Path | Purpose |
| --- | --- |
| [docker-compose.yml](docker-compose.yml) | Local Postgres + API + Web with mocked services |
| [.github/workflows/ci.yml](.github/workflows/ci.yml) | Lint/test backend, build frontend, `docker compose build` |
| [.github/workflows/deploy-azure.yml](.github/workflows/deploy-azure.yml) | Deploy to Azure App Service on push to `main` |
| [infra/bicep/main.bicep](infra/bicep/main.bicep) | Minimal Azure IaC (App Service, PostgreSQL, Storage, Key Vault) |
| [infra/monitoring.md](infra/monitoring.md) | App Insights, alerts, dashboards |
| [infra/backup.md](infra/backup.md) | PostgreSQL PITR and blob backup/restore |

## License

Proprietary — © VyaparAI. All rights reserved.
