# 1. Product Requirements Document (PRD)

**Product:** KuberAIQ — AI Business Manager for Indian MSMEs
**Version:** 1.0 (Phase 1 MVP)
**Owner:** Principal Product Manager
**Status:** Approved for build

---

## 1.1 Vision

Give every Indian MSME owner a trustworthy AI "business manager" that runs the
back-office (invoicing, collections, GST, cash flow, customers) through natural
language on the channels they already use — **WhatsApp**, **web**, and **voice** —
so they can spend time selling, not on paperwork.

## 1.2 Problem statement

India has ~63 million MSMEs. Owners typically:

- Create invoices manually (Excel / paper / Tally), often with GST errors.
- Chase payments over WhatsApp/phone with no system of record.
- Have **no real-time view** of who owes them money or their cash position.
- Lose hours each week on repetitive admin instead of growing the business.

Existing tools (Tally, Zoho, Vyapar app) are **form-driven** and assume accounting
literacy. They are not conversational, not WhatsApp-native, and not proactive.

## 1.3 Target users (personas)

| Persona | Description | Primary need |
| --- | --- | --- |
| **Ramesh** — Owner (primary) | 38, runs a building-materials trading shop, 40-tier-2 city. Comfortable on WhatsApp, not on accounting software. | "Just tell me who hasn't paid and send them a reminder." |
| **Priya** — Office staff/accountant | 28, manages invoices and follow-ups for the owner. | Fast invoice creation, accurate GST, clean reports. |
| **Anil** — Vendor/CA (secondary, post-MVP) | Chartered Accountant who consumes GST reports. | Correct GSTR-ready data export. |

## 1.4 Goals & success metrics (Phase 1)

| Goal | Metric | Target (90 days post-launch) |
| --- | --- | --- |
| Reduce admin time | Median time to create + send an invoice | < 60 seconds |
| Improve collections | % overdue invoices with at least one reminder sent | > 90% |
| Drive engagement | Weekly active businesses using AI copilot | > 60% of signups |
| Data accuracy | GST calculation error rate | < 0.1% |
| Trust | AI action confirmation rate (no wrong action committed) | > 99% |

**North-star metric:** *Rupees of receivables collected per active business per month.*

## 1.5 Scope

### In scope (Phase 1 MVP — 5 modules)

1. **Invoice Management** — create, edit, cancel, view, search, GST calc, auto numbering, PDF, WhatsApp share.
2. **Customer Management** — CRUD, search, payment history.
3. **Collections** — overdue detection, reminder generation, WhatsApp automation, dashboard.
4. **Business Dashboard** — revenue, pending, overdue, aging, cash-flow summary.
5. **AI Copilot** — intent understanding, entity extraction, tool calling, response (WhatsApp + web + voice text).

### Out of scope (Phase 1 — deferred)

- Full double-entry accounting / P&L / balance sheet.
- Inventory & stock management.
- E-invoicing IRN/e-way bill integration with GSTN (planned Phase 2).
- Payment gateway collection (UPI deep-link only in Phase 2).
- Multi-currency, multi-language UI beyond English + Hindi text.
- Native mobile apps (web is mobile-responsive PWA in Phase 1).

## 1.6 Key product principles

1. **Conversation-first, form-fallback.** Anything doable by chat is also doable by UI.
2. **Confirm before commit.** AI never finalizes a money-affecting action (invoice, reminder send) without an explicit confirm.
3. **Correct over clever.** GST and money math are deterministic in code, never "guessed" by the LLM.
4. **WhatsApp is a first-class channel,** not an afterthought.
5. **Trust & auditability.** Every state change is attributable and logged.

## 1.7 High-level user journeys

1. **Onboard:** Sign in with Microsoft Entra ID → create company profile (GSTIN, address) → add first customer.
2. **Invoice via chat:** "Invoice ABC Traders, 50 bags cement @ ₹350, 18% GST" → AI drafts → owner confirms → PDF + WhatsApp.
3. **Collect:** Dashboard shows ₹2.3L overdue → "Send reminders to everyone overdue" → AI lists, owner confirms → WhatsApp reminders sent.
4. **Insight:** "What's my cash flow next month?" → AI returns expected inflows from due invoices + confidence note.

## 1.8 Release criteria (Definition of Done for MVP)

- All 5 modules functional end-to-end on web + WhatsApp.
- ≥ 80% automated test coverage on backend domain + services.
- Security review passed (OWASP ASVS L1, prompt-injection guardrails).
- p95 API latency < 400 ms (non-AI), < 4 s (AI copilot).
- Deployed to Azure with CI/CD, monitoring, and backups configured.

## 1.9 Risks & mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| LLM hallucinates amounts/GST | Financial errors, lost trust | Deterministic calc in code; LLM only extracts entities; confirm-before-commit |
| Prompt injection via customer name/notes | Data exfiltration / wrong actions | Input sanitization, tool allow-list, output schema validation (see Security doc) |
| WhatsApp API template approval delays | Reminders blocked | Pre-approve templates; SMS/email fallback channel abstraction |
| GST rule changes | Incorrect tax | Externalize GST rates to config table; versioned tax rules |
| Azure OpenAI quota/cost | Outage / overspend | Token budgets per tenant, caching, rate limits, graceful degradation to forms |
