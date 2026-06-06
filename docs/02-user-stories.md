# 2. User Stories

Format: `As a <role>, I want <capability>, so that <benefit>.`
Each story has acceptance criteria (AC) in Given/When/Then. IDs map to epics.

Roles: **OWN** = Owner, **STF** = Office staff, **SYS** = System/AI.

---

## Epic A — Authentication & Onboarding

### US-A1 — Sign in with Microsoft
**As an** owner, **I want** to sign in with my Microsoft account, **so that** I don't manage another password.
- **AC1** Given a valid Entra ID account, when I complete OIDC login, then I receive a session and land on the dashboard.
- **AC2** Given a first-time user, when login succeeds, then a `users` row is created and I am prompted to create a company.
- **AC3** Given an expired token, when I call any API, then I get `401` and am redirected to login.

### US-A2 — Create company profile
**As an** owner, **I want** to set up my company (name, GSTIN, address, state), **so that** invoices are GST-compliant.
- **AC1** GSTIN is validated against the 15-char checksum format; invalid input is rejected with a clear message.
- **AC2** State code is derived from GSTIN and stored for CGST/SGST vs IGST logic.

---

## Epic B — Customer Management (Module 2)

### US-B1 — Create customer
**As** staff, **I want** to add a customer with name, phone, GSTIN, address, **so that** I can invoice them.
- **AC1** Phone is validated as a 10-digit Indian mobile (optionally +91).
- **AC2** Duplicate detection warns if a customer with the same phone exists in the company.

### US-B2 — Edit / delete customer
**As** staff, **I want** to edit or soft-delete a customer, **so that** records stay accurate.
- **AC1** Delete is a soft-delete (sets `deleted_at`); customers with invoices cannot be hard-deleted.

### US-B3 — Search customer
**As** staff, **I want** to search customers by name/phone, **so that** I find them fast.
- **AC1** Search is case-insensitive, partial match, paginated, scoped to my company.

### US-B4 — Customer payment history
**As an** owner, **I want** to see a customer's invoices and payments, **so that** I know their standing.
- **AC1** Shows total billed, total paid, outstanding, and aging buckets.

---

## Epic C — Invoice Management (Module 1)

### US-C1 — Create invoice
**As** staff, **I want** to create an invoice with line items and GST, **so that** I can bill a customer.
- **AC1** Invoice number is auto-generated, sequential per company per financial year, gap-free.
- **AC2** GST is computed in code: intra-state → CGST+SGST, inter-state → IGST, using the customer/company state.
- **AC3** Totals (taxable, tax, grand total) are stored and never trusted from the client.

### US-C2 — Edit invoice
**As** staff, **I want** to edit a draft invoice, **so that** I can fix mistakes.
- **AC1** Only `DRAFT` invoices are editable; `ISSUED`/`PAID`/`CANCELLED` are immutable (a credit/new invoice is required).

### US-C3 — Cancel invoice
**As an** owner, **I want** to cancel an invoice, **so that** wrong bills are voided.
- **AC1** Cancellation sets status `CANCELLED`, requires a reason, and writes an audit log; payments block cancellation.

### US-C4 — View & search invoices
**As** staff, **I want** to list/search/filter invoices, **so that** I track billing.
- **AC1** Filter by status, customer, date range; sort by date/amount; paginated.

### US-C5 — PDF generation
**As** staff, **I want** a professional PDF, **so that** I can share a proper bill.
- **AC1** PDF includes company + customer GSTIN, HSN, per-line and total GST split, invoice number, due date.
- **AC2** PDF is stored in Blob Storage; a signed URL is returned.

### US-C6 — Share on WhatsApp
**As an** owner, **I want** to send the invoice on WhatsApp, **so that** the customer receives it instantly.
- **AC1** Sends an approved template with the PDF link to the customer's phone; logs the send.

---

## Epic D — Collections (Module 3)

### US-D1 — Detect overdue
**As the** system, **I want** to flag invoices past due date and unpaid, **so that** they surface for collection.
- **AC1** A scheduled job marks invoices `OVERDUE` when `due_date < today` and balance > 0.

### US-D2 — Generate reminder
**As an** owner, **I want** AI to draft a polite reminder, **so that** I don't write each one.
- **AC1** Reminder references invoice number, amount due, days overdue; tone is polite and professional; available in English/Hindi.

### US-D3 — Send WhatsApp reminder (single & bulk)
**As an** owner, **I want** to send reminders to one or all overdue customers, **so that** I collect faster.
- **AC1** Bulk send requires explicit confirmation showing count and total amount; each send is rate-limited and logged in `reminders`.

### US-D4 — Collections dashboard
**As an** owner, **I want** a collections view, **so that** I prioritize follow-ups.
- **AC1** Lists overdue invoices sorted by amount/days; shows last reminder date and channel.

---

## Epic E — Business Dashboard (Module 4)

### US-E1 — Revenue & receivables
**As an** owner, **I want** revenue, pending, and overdue totals, **so that** I know my position at a glance.
### US-E2 — Aging report
**As an** owner, **I want** a 0-30 / 31-60 / 61-90 / 90+ aging report, **so that** I see risk concentration.
### US-E3 — Cash-flow summary
**As an** owner, **I want** expected inflows from due invoices, **so that** I can plan.
- **AC1** Cash-flow projection is computed from invoice due dates and balances, with an explicit "expected, not guaranteed" disclaimer.

---

## Epic F — AI Copilot (Module 5)

### US-F1 — Natural-language intent
**As an** owner, **I want** to type/say a request in plain language, **so that** I don't navigate menus.
- **AC1** "Show unpaid invoices", "Who hasn't paid me", "Generate invoice for Raj Traders", "How much is pending" are correctly routed.

### US-F2 — Entity extraction & confirmation
**As an** owner, **I want** the AI to extract customer/items/amounts and confirm before acting, **so that** mistakes are caught.
- **AC1** For any write action, the AI shows a structured summary and waits for "yes/confirm".

### US-F3 — Tool calling
**As the** system, **I want** the AI to call typed tools (create_invoice, find_overdue, ...), **so that** business logic stays deterministic.
- **AC1** Tools validate inputs server-side; the LLM never computes money.

### US-F4 — Multi-channel
**As an** owner, **I want** the same copilot on WhatsApp and web, **so that** the experience is consistent.

---

## Epic G — Audit & Security (cross-cutting)

### US-G1 — Audit trail
**As an** admin, **I want** every create/update/cancel/send recorded with actor, time, before/after, **so that** actions are traceable.
### US-G2 — Tenant isolation
**As an** owner, **I want** to only ever see my company's data, **so that** my business is private.
- **AC1** Every query is scoped by `company_id`; attempts to access other tenants return `404/403`.
