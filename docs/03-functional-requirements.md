# 3. Functional Requirements (FR)

Each requirement is testable. `FR-<module>-<n>`. Priority: **M**=Must, **S**=Should, **C**=Could.

---

## 3.1 Authentication & Tenancy (AUTH)

| ID | Pri | Requirement |
| --- | --- | --- |
| FR-AUTH-1 | M | The system SHALL authenticate users via Microsoft Entra ID (OIDC authorization-code + PKCE). |
| FR-AUTH-2 | M | The backend SHALL validate Entra-issued tokens (issuer, audience, signature, expiry) and mint a short-lived app JWT (access 15 min) + refresh (7 days, rotating). |
| FR-AUTH-3 | M | Every authenticated user SHALL belong to exactly one company in MVP (multi-company deferred). |
| FR-AUTH-4 | M | All data access SHALL be scoped by `company_id` (row-level tenant isolation). |
| FR-AUTH-5 | M | The system SHALL support roles: `OWNER`, `STAFF`, `VIEWER` (RBAC). |

## 3.2 Customer Management (CUST)

| ID | Pri | Requirement |
| --- | --- | --- |
| FR-CUST-1 | M | Create a customer with: name (req), phone (req), email, GSTIN, billing address, state code, notes. |
| FR-CUST-2 | M | Validate phone (Indian 10-digit, optional +91) and GSTIN (15-char format + checksum) when provided. |
| FR-CUST-3 | M | Edit any customer field; changes are audited. |
| FR-CUST-4 | M | Soft-delete a customer (set `deleted_at`); block delete if active (non-cancelled) invoices exist. |
| FR-CUST-5 | M | Search/list customers by name/phone (partial, case-insensitive), paginated, company-scoped. |
| FR-CUST-6 | M | Return a customer's payment history: invoices, payments, total billed/paid/outstanding, aging. |
| FR-CUST-7 | S | Warn on duplicate phone within the same company at create time. |

## 3.3 Invoice Management (INV)

| ID | Pri | Requirement |
| --- | --- | --- |
| FR-INV-1 | M | Create an invoice with customer, issue date, due date, and ≥1 line item (description, HSN/SAC, qty, unit price, GST rate). |
| FR-INV-2 | M | Auto-generate a unique, gap-free, sequential invoice number per company per financial year: `<PREFIX>/<FY>/<NNNN>` (e.g. `INV/2025-26/0042`). |
| FR-INV-3 | M | Compute GST in code: if customer state == company state → CGST + SGST (rate/2 each); else IGST (full rate). Per-line and invoice totals. |
| FR-INV-4 | M | Persist taxable amount, CGST, SGST, IGST, total tax, grand total, rounding adjustment, and amount due. Client-supplied totals SHALL be ignored. |
| FR-INV-5 | M | Invoice lifecycle states: `DRAFT → ISSUED → (PARTIALLY_PAID) → PAID`; plus `OVERDUE`, `CANCELLED`. |
| FR-INV-6 | M | Edit allowed only in `DRAFT`. Issued invoices are immutable except via cancel + reissue or credit note (Phase 2). |
| FR-INV-7 | M | Cancel an invoice (requires reason); blocked if any payment recorded. Writes audit log. |
| FR-INV-8 | M | View a single invoice and list/search/filter invoices (status, customer, date range), sortable, paginated. |
| FR-INV-9 | M | Generate a GST-compliant PDF (company+customer GSTIN, HSN, tax split, totals in words) via ReportLab; store in Blob; return signed URL. |
| FR-INV-10 | M | Share invoice PDF link to customer via WhatsApp template message; log the send. |
| FR-INV-11 | S | Generate a GST summary report (taxable, CGST, SGST, IGST totals) for a date range, exportable as CSV. |

## 3.4 Payments (PAY)

| ID | Pri | Requirement |
| --- | --- | --- |
| FR-PAY-1 | M | Record a payment against an invoice: amount, date, method (cash/UPI/bank/cheque), reference. |
| FR-PAY-2 | M | A payment SHALL update invoice `amount_due` and transition status to `PARTIALLY_PAID` or `PAID`. |
| FR-PAY-3 | M | Reject payments exceeding the outstanding balance. |
| FR-PAY-4 | S | Support deleting/reversing a payment with audit trail (correction). |

## 3.5 Collections (COLL)

| ID | Pri | Requirement |
| --- | --- | --- |
| FR-COLL-1 | M | A scheduled job SHALL mark issued, unpaid invoices `OVERDUE` when `due_date < today`. |
| FR-COLL-2 | M | Generate a reminder message (AI-assisted) referencing invoice no., amount due, days overdue; English & Hindi. |
| FR-COLL-3 | M | Send a reminder to a single customer via WhatsApp; record in `reminders` with status. |
| FR-COLL-4 | M | Bulk-send reminders to all overdue customers after explicit confirmation (count + total shown). |
| FR-COLL-5 | M | Collections dashboard: overdue invoices sorted by amount/days, last reminder date/channel. |
| FR-COLL-6 | S | Respect a per-customer reminder cooldown (no more than 1 reminder / 48h by default). |

## 3.6 Dashboard (DASH)

| ID | Pri | Requirement |
| --- | --- | --- |
| FR-DASH-1 | M | Show total revenue (paid) for a selectable period. |
| FR-DASH-2 | M | Show total pending (issued, not yet due) and total overdue receivables. |
| FR-DASH-3 | M | Show customer aging report: 0-30 / 31-60 / 61-90 / 90+ days buckets. |
| FR-DASH-4 | M | Show cash-flow summary: expected inflows by week/month from due invoices (clearly labelled "expected"). |
| FR-DASH-5 | S | Show top customers by revenue and top overdue customers. |

## 3.7 AI Copilot (AI)

| ID | Pri | Requirement |
| --- | --- | --- |
| FR-AI-1 | M | Accept a natural-language message (web text, WhatsApp text, transcribed voice) and a conversation context. |
| FR-AI-2 | M | Classify intent and route to the correct agent (Invoice / Collections / Dashboard / Customer). |
| FR-AI-3 | M | Extract entities (customer name, items, qty, price, GST rate, dates, amounts) into a typed schema. |
| FR-AI-4 | M | Execute business actions ONLY through registered, server-validated tools (no direct DB writes by the LLM). |
| FR-AI-5 | M | For any write/money action, return a structured confirmation and require explicit user confirmation before commit. |
| FR-AI-6 | M | Return responses as structured JSON (message + optional data payload + suggested actions) rendered by clients. |
| FR-AI-7 | M | Enforce guardrails: prompt-injection filtering, tool allow-listing, output schema validation, and GST/amount validation. |
| FR-AI-8 | S | Maintain short-term conversation memory per session (last N turns) for follow-ups ("send it to them"). |
| FR-AI-9 | C | Voice: accept audio, transcribe (Azure Speech), process as text; reply with text (TTS optional Phase 2). |

## 3.8 Notifications (NOTIF)

| ID | Pri | Requirement |
| --- | --- | --- |
| FR-NOTIF-1 | M | Integrate WhatsApp Business Cloud API for outbound template + session messages. |
| FR-NOTIF-2 | M | Provide a channel-abstraction interface so SMS/email can be added without changing callers. |
| FR-NOTIF-3 | M | Handle inbound WhatsApp webhooks (message received, status callbacks) with signature verification. |

## 3.9 Audit (AUDIT)

| ID | Pri | Requirement |
| --- | --- | --- |
| FR-AUDIT-1 | M | Record every create/update/cancel/send/payment with actor, company, entity, action, before/after JSON, timestamp, IP. |
| FR-AUDIT-2 | M | Audit logs SHALL be append-only and queryable by company + entity. |
