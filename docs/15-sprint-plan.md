# 15. Sprint Plan

2-week sprints, ~40 story points/sprint (team of 10, but parallelised). Phase-1 MVP = 6 sprints (~12 weeks).
Story IDs reference Doc 2 (User Stories).

---

## Sprint 0 — Foundations (M0)
**Goal:** Walking skeleton deployable to Azure with auth and DB.

| Item | Pts | Owner |
| --- | --- | --- |
| Monorepo, pyproject, Next app, Tailwind/shadcn init | 3 | DevOps/React |
| Docker Compose (Postgres + api + web) | 3 | DevOps |
| SQLAlchemy base, Alembic, initial migration (all tables) | 5 | FastAPI/DBA |
| Core: config, constants, logging, errors, DI container | 5 | FastAPI |
| Auth: Entra OIDC + mock auth + JWT (US-A1, US-A2) | 8 | FastAPI/Azure |
| CI: lint, typecheck, tests, coverage gate | 5 | DevOps |
| Bicep skeleton (network, pg, app service, kv) | 5 | Azure |
| Health endpoints + App Insights wiring | 3 | DevOps |
**Total: 37**

## Sprint 1 — Customers + Invoice domain (M1, start M2)
**Goal:** Customer module end-to-end; GST engine proven.

| Item | Pts | Owner |
| --- | --- | --- |
| Domain VOs: Money, GSTIN, Phone, GstBreakup | 5 | FastAPI |
| GstCalculator domain service + exhaustive unit tests | 5 | FastAPI/QA |
| Customer entity/repo/service + API (US-B1..B5) | 8 | FastAPI |
| Customer payment history (US-B4) | 3 | FastAPI |
| Frontend: app shell, sidebar, theme, login (US-A1) | 5 | React |
| Frontend: Customers list + form + detail | 8 | React |
| Tests: customer service/api ≥80% | 3 | QA |
**Total: 37**

## Sprint 2 — Invoices (M2)
**Goal:** Full invoice lifecycle + PDF.

| Item | Pts | Owner |
| --- | --- | --- |
| Invoice aggregate, numbering policy, repo, UoW | 8 | FastAPI/DBA |
| InvoiceService: create/edit/issue/cancel (US-C1..C4) | 8 | FastAPI |
| ReportLab PDF generator + Blob/local storage (US-C5) | 5 | FastAPI |
| Payments: record/reverse + status transitions (FR-PAY) | 5 | FastAPI |
| Frontend: invoice list/filters + create/view (US-C1,C4) | 8 | React |
| Tests: invoice domain/service/api | 3 | QA |
**Total: 37**

## Sprint 3 — Collections + WhatsApp (M3)
**Goal:** Overdue detection + reminders over WhatsApp.

| Item | Pts | Owner |
| --- | --- | --- |
| Notifier port + WhatsApp adapter + mock notifier | 5 | FastAPI/Azure |
| Invoice WhatsApp share (US-C6) | 3 | FastAPI |
| Overdue scheduler job (US-D1, FR-COLL-1) | 5 | FastAPI/DevOps |
| Reminder generation + single/bulk send (US-D2,D3) | 8 | FastAPI |
| WhatsApp webhook (verify + inbound) | 5 | FastAPI |
| Frontend: collections dashboard + bulk confirm (US-D4) | 8 | React |
| Tests: collections + notifier mocks | 3 | QA |
**Total: 37**

## Sprint 4 — Dashboard + AI Copilot core (M4, start M5)
**Goal:** Metrics dashboard + routing + first agent.

| Item | Pts | Owner |
| --- | --- | --- |
| DashboardService: revenue/pending/overdue/aging/cashflow | 8 | FastAPI/DBA |
| Frontend: dashboard cards + charts (US-E1..E3) | 8 | React |
| LangGraph state, router, mock LLM, guardrails | 8 | AI Arch |
| Invoice + Customer agents + tools + confirm flow | 8 | AI Arch/FastAPI |
| `/ai/chat` endpoint + session checkpointer | 5 | FastAPI |
**Total: 37**

## Sprint 5 — AI Copilot complete + hardening (M5, M6)
**Goal:** All 4 agents, real Azure OpenAI, security & perf hardening.

| Item | Pts | Owner |
| --- | --- | --- |
| Collections + Dashboard agents + tools | 8 | AI Arch |
| Azure OpenAI adapter + prompts + token budgets | 5 | AI Arch/Azure |
| Frontend: Assistant chat UI + confirm cards + voice input | 8 | React |
| Rate limiting, security headers, RBAC audit, pen-test fixes | 8 | Sol Arch/DevOps |
| Observability: traces, dashboards, alerts; load test | 5 | DevOps/QA |
| E2E (Playwright) + agent tests; coverage to ≥80% | 3 | QA |
**Total: 37**

## Sprint 6 — Beta launch (M7)
**Goal:** Production deploy + pilot onboarding.

| Item | Pts | Owner |
| --- | --- | --- |
| Production Bicep + Front Door/WAF + private endpoints | 8 | Azure |
| CD to production w/ approval + migrations + smoke | 5 | DevOps |
| DR drill (PITR restore) + backup verification | 3 | Azure/DBA |
| Onboarding flow polish, empty states, help content | 5 | UX/React |
| Pilot with 5 businesses, feedback loop, bug bash | 8 | PM/QA/all |
| Docs: runbooks, support playbook | 3 | DevOps |
**Total: 32**

---

## Definition of Ready / Done

**Ready:** story has AC, design/API contract, test notes, and is estimated.
**Done:** merged behind green CI, ≥80% coverage on touched domain/service code, migration
written, observability added, docs/OpenAPI updated, demoed in sprint review.

## Ceremonies

Planning (Mon W1), daily stand-up, backlog refinement (Wed W1), sprint review + retro
(Fri W2). AI safety review is a standing agenda item every sprint.
