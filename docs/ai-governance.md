# KuberAIQ AI Governance

Aligned with ISO/IEC 42001 principles for AI management systems. This document is the living inventory for the KuberAIQ copilot and related automation.

## 1. AI system inventory

| System | Purpose | Model / engine | Data accessed | Channels |
| --- | --- | --- | --- | --- |
| MSME Copilot | Invoice, collections, dashboard Q&A | Azure OpenAI (gpt-4o) or deterministic mock | Tenant invoices, customers, products, compliance summary | Web `/assistant`, WhatsApp inbound |
| Intent router | Classify user message → agent route | Same LLM stack | User message only | Internal |
| Entity extractor | Parse invoice/customer slots | Same LLM stack | User message + catalog hints | Internal |
| Compliance alerts | Scheduled obligation reminders | Rule engine + optional WhatsApp | Compliance obligations, company profile | WhatsApp, email (stub) |
| Payment reminders | Overdue / due-soon nudges | Template messages (en/hi) | Invoice, customer phone | WhatsApp |

## 2. Roles and accountability

| Role | Responsibility |
| --- | --- |
| Platform admin | Tenant suspend/activate, AI usage review, integration mode verification |
| Business owner (OWNER) | Approves AI actions that mutate data; manages billing and integrations |
| Staff (STAFF) | Uses copilot and operational APIs within RBAC matrix; cannot cancel invoices or change company/billing |
| CA advisor | Read-only client workspace; filing checklist; no MSME write APIs |
| Engineering | Model deployment, prompt changes, token budgets, audit retention |

## 3. Human-in-the-loop (confirm actions)

Destructive or financial mutations require explicit confirmation in the web copilot:

- Create invoice / credit note
- Send payment reminder (single or bulk)
- Create customer

The API exposes `requires_confirmation` and `/ai/confirm`. WhatsApp copilot uses the same graph; high-risk tools are not auto-executed without confirmation semantics in session state.

## 4. Risk mitigations

| Risk | Mitigation |
| --- | --- |
| Wrong customer or amount on invoice | Confirm card with preview; audit log on issue |
| Cross-tenant data leak | JWT + `company_id` on every query; verified auth context |
| Unbounded LLM cost | Monthly token budget (`AI_SOFT_TOKEN_BUDGET_MONTHLY`); usage logged in `ai_usage_log` |
| Prompt injection | System prompts scoped to business tasks; tool allow-list per agent |
| PII in logs | Structured logs avoid raw message bodies in production |
| Mock vs live confusion | `/health/integrations` reports `llm_mode`, `whatsapp_mode`, `billing_mode` |

## 5. Logging and monitoring

- **AI usage**: `ai_usage_log` per company (tokens in/out, session id, model name)
- **Audit trail**: `audit_logs` for invoice issue, payment, reminder, admin tenant actions
- **Admin portal**: cross-tenant AI usage and system health endpoints
- **Alerts**: rate limits on `/ai/*`; subscription gate when live billing enabled

## 6. Change control

- Prompt changes: `backend/app/infrastructure/ai/prompts/`
- Model deployment: `AZURE_OPENAI_*` env vars; `USE_MOCK_LLM=false` when creds present
- Feature flags: `USE_MOCK_LLM`, `USE_MOCK_WHATSAPP`, `USE_MOCK_BILLING`

Last updated: June 2026.
