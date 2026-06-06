# 4. Non-Functional Requirements (NFR)

`NFR-<area>-<n>`. These are measurable quality attributes and operational constraints.

---

## 4.1 Performance & scalability

| ID | Requirement | Target |
| --- | --- | --- |
| NFR-PERF-1 | p95 latency for CRUD/read APIs (non-AI) | < 400 ms |
| NFR-PERF-2 | p95 latency for AI copilot turn (incl. LLM) | < 4 s |
| NFR-PERF-3 | PDF generation time | < 2 s per invoice |
| NFR-PERF-4 | Sustained throughput per backend instance | ≥ 100 req/s |
| NFR-PERF-5 | Horizontal scale | Stateless API; scale out on Azure App Service (2–10 instances autoscale on CPU/queue depth) |
| NFR-PERF-6 | DB connection pooling | SQLAlchemy async pool (size tuned per instance); pgbouncer-ready |

## 4.2 Availability & reliability

| ID | Requirement | Target |
| --- | --- | --- |
| NFR-AVL-1 | Monthly availability (API) | 99.5% |
| NFR-AVL-2 | RPO (data loss tolerance) | ≤ 15 min (PITR) |
| NFR-AVL-3 | RTO (recovery time) | ≤ 1 hour |
| NFR-AVL-4 | Graceful degradation: if Azure OpenAI is unavailable, the copilot returns a fallback message and forms remain fully usable. |
| NFR-AVL-5 | All external calls (LLM, WhatsApp, Blob) wrapped with timeouts, retries (exponential backoff + jitter), and circuit breakers. |
| NFR-AVL-6 | Idempotency keys on write endpoints and on outbound notification sends to prevent duplicates. |

## 4.3 Security & privacy (summary — see Doc 12)

| ID | Requirement |
| --- | --- |
| NFR-SEC-1 | OWASP ASVS Level 1 compliance; OWASP Top 10 mitigations documented and tested. |
| NFR-SEC-2 | All traffic over TLS 1.2+; HSTS enforced. |
| NFR-SEC-3 | Secrets in Azure Key Vault; no secrets in code, images, or logs. |
| NFR-SEC-4 | Data encrypted at rest (Azure-managed keys) and in transit. |
| NFR-SEC-5 | RBAC enforced server-side on every endpoint; tenant isolation by `company_id`. |
| NFR-SEC-6 | Rate limiting (per IP + per user + per tenant) on all public endpoints; stricter on `/auth` and `/ai/chat`. |
| NFR-SEC-7 | Prompt-injection protection and tool allow-listing for the AI layer. |
| NFR-SEC-8 | PII (phone, GSTIN, address) access audited; data retention & deletion policy defined. |

## 4.4 Maintainability & code quality

| ID | Requirement |
| --- | --- |
| NFR-MNT-1 | Clean Architecture layering: `domain` has zero framework/infra imports. |
| NFR-MNT-2 | ≥ 80% automated test coverage on backend `domain` + `services`. |
| NFR-MNT-3 | Static analysis: `ruff` (lint), `black` (format), `mypy --strict` on `domain`/`application`; `eslint` + `prettier` + `tsc --noEmit` on frontend. |
| NFR-MNT-4 | All magic/static values centralized in constants modules (`backend/app/core/constants.py`, `frontend/src/lib/constants.ts`). |
| NFR-MNT-5 | Conventional Commits; PRs require green CI + 1 review. |
| NFR-MNT-6 | OpenAPI schema auto-generated and published; typed client generated for frontend. |

## 4.5 Observability

| ID | Requirement |
| --- | --- |
| NFR-OBS-1 | Structured JSON logging with correlation/request IDs and `company_id` (no PII/secrets in logs). |
| NFR-OBS-2 | Distributed tracing (OpenTelemetry → Azure Monitor / Application Insights). |
| NFR-OBS-3 | Metrics: request rate, latency, error rate, LLM token usage & cost per tenant, WhatsApp send success rate. |
| NFR-OBS-4 | Alerting on error-rate spikes, latency SLO breaches, LLM/WhatsApp failures, DB connection saturation. |
| NFR-OBS-5 | `/health` (liveness) and `/health/ready` (readiness: DB + dependencies) endpoints. |

## 4.6 Cost & AI governance

| ID | Requirement |
| --- | --- |
| NFR-COST-1 | Per-tenant monthly LLM token budget with soft + hard caps; degrade gracefully at hard cap. |
| NFR-COST-2 | Cache deterministic AI responses & embeddings where safe; prefer cheap models for routing/classification. |
| NFR-COST-3 | Track and attribute LLM cost per company for billing/analytics. |

## 4.7 Compliance & localization

| ID | Requirement |
| --- | --- |
| NFR-CMP-1 | GST invoices conform to CGST Rules formatting (mandatory fields, tax split, HSN). |
| NFR-CMP-2 | Data residency: store data in an India Azure region (Central/South India). |
| NFR-CMP-3 | Localization: UI English (Phase 1) with Hindi support for AI messages & reminders; currency INR, IST timezone, Indian FY (Apr–Mar). |

## 4.8 Configuration & environments

| ID | Requirement |
| --- | --- |
| NFR-CFG-1 | 12-factor config via environment variables; no env-specific code branches. |
| NFR-CFG-2 | Environments: `local`, `dev`, `staging`, `production`. |
| NFR-CFG-3 | External services mockable via env toggles for local dev (see below). |

### External-service toggles (local dev)

| Toggle (env var) | Default (local) | Effect |
| --- | --- | --- |
| `USE_MOCK_LLM` | `true` | Use a deterministic in-process LLM stub instead of Azure OpenAI. |
| `USE_MOCK_BLOB` | `true` | Store PDFs on local disk (`local_blob_storage/`) instead of Azure Blob. |
| `USE_MOCK_WHATSAPP` | `true` | Log WhatsApp sends to console/DB instead of calling the real API. |
| `USE_MOCK_AUTH` | `true` | Issue dev JWTs for a seeded user instead of full Entra OIDC. |

> In `staging`/`production` all toggles default to `false` and real services are required.
