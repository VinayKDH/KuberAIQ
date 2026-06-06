# 9. API Specifications

Base URL: `/api/v1`. All responses are JSON. Auth via `Authorization: Bearer <jwt>`
(except `/auth/*`, `/health`, and the WhatsApp webhook which uses signature verification).

## 9.1 Conventions

### Standard error envelope

```json
{
  "error": {
    "code": "INVOICE_NOT_EDITABLE",
    "message": "Only DRAFT invoices can be edited.",
    "details": [{"field": "status", "issue": "must be DRAFT"}],
    "request_id": "b1f2...."
  }
}
```

| HTTP | When |
| --- | --- |
| 200/201 | success |
| 400 | validation error (`VALIDATION_ERROR`) |
| 401 | missing/invalid token |
| 403 | authenticated but not permitted (RBAC / tenant) |
| 404 | not found (also used to hide cross-tenant resources) |
| 409 | conflict (duplicate, invalid state transition) |
| 422 | semantic validation (FastAPI/pydantic) |
| 429 | rate limited (`Retry-After` header) |
| 500 | unexpected (no internal details leaked) |

### Pagination (list endpoints)

Query: `?page=1&page_size=20&sort=-issue_date&q=<search>`

```json
{ "items": [ ... ], "page": 1, "page_size": 20, "total": 134 }
```

### Idempotency

Write endpoints accept `Idempotency-Key` header; repeated keys return the original result.

---

## 9.2 Auth

### `POST /auth/callback`
Exchange Entra authorization code for app tokens.

Request:
```json
{ "code": "0.AX...", "code_verifier": "dBj...", "redirect_uri": "https://app/callback" }
```
Response `200`:
```json
{ "access_token": "ey...", "refresh_token": "ey...", "token_type": "bearer", "expires_in": 900,
  "user": { "id": "uuid", "email": "ramesh@abc.in", "full_name": "Ramesh", "role": "OWNER", "company_id": "uuid" } }
```

### `POST /auth/refresh`  → new access token (rotates refresh).
### `POST /auth/logout`  → revokes refresh token.
### `GET  /auth/me`      → current user + company.

---

## 9.3 Customers

| Method | Path | Description | Roles |
| --- | --- | --- | --- |
| POST | `/customers` | Create customer | OWNER, STAFF |
| GET | `/customers` | List/search (`q`, paginated) | all |
| GET | `/customers/{id}` | Get one | all |
| PATCH | `/customers/{id}` | Update | OWNER, STAFF |
| DELETE | `/customers/{id}` | Soft-delete | OWNER |
| GET | `/customers/{id}/history` | Payment history + aging | all |

`POST /customers` request:
```json
{ "name": "ABC Traders", "phone": "9876543210", "email": "abc@traders.in",
  "gstin": "27ABCDE1234F1Z5", "billing_address": "MIDC, Pune", "notes": "" }
```
Response `201`:
```json
{ "id": "uuid", "name": "ABC Traders", "phone": "9876543210", "gstin": "27ABCDE1234F1Z5",
  "state_code": "27", "created_at": "2026-06-06T05:30:00Z" }
```
Validation: `name` 1–200; `phone` Indian 10-digit (normalised, `+91` stripped);
`gstin` optional, 15-char checksum-validated; `state_code` derived from GSTIN.

---

## 9.4 Invoices

| Method | Path | Description |
| --- | --- | --- |
| POST | `/invoices` | Create (DRAFT or ISSUED) |
| GET | `/invoices` | List/search/filter (`status`, `customer_id`, `from`, `to`, `q`) |
| GET | `/invoices/{id}` | Get one (with items) |
| PATCH | `/invoices/{id}` | Edit (DRAFT only) |
| POST | `/invoices/{id}:issue` | DRAFT → ISSUED (allocates number) |
| POST | `/invoices/{id}:cancel` | Cancel (reason required) |
| POST | `/invoices/{id}/payments` | Record payment |
| GET | `/invoices/{id}/pdf` | Generate/fetch PDF (signed URL) |
| POST | `/invoices/{id}:share-whatsapp` | Send PDF to customer on WhatsApp |
| GET | `/invoices/reports/gst` | GST summary for date range (CSV/JSON) |

`POST /invoices` request:
```json
{
  "customer_id": "uuid",
  "issue_date": "2026-06-06",
  "due_date": "2026-06-21",
  "status": "ISSUED",
  "items": [
    { "description": "OPC 53 Grade Cement", "hsn_sac": "2523", "quantity": 50,
      "unit": "BAG", "unit_price": 350.00, "gst_rate": 18 }
  ]
}
```
Server computes GST (CGST/SGST vs IGST from states), totals, number. Response `201`:
```json
{
  "id": "uuid", "invoice_number": "INV/2025-26/0042", "status": "ISSUED",
  "customer": { "id": "uuid", "name": "ABC Traders" },
  "issue_date": "2026-06-06", "due_date": "2026-06-21",
  "items": [ { "line_no": 1, "description": "OPC 53 Grade Cement", "hsn_sac": "2523",
    "quantity": 50, "unit_price": 350.0, "gst_rate": 18, "taxable_amount": 17500.0,
    "cgst_amount": 1575.0, "sgst_amount": 1575.0, "igst_amount": 0.0, "line_total": 20650.0 } ],
  "taxable_amount": 17500.0, "cgst_amount": 1575.0, "sgst_amount": 1575.0,
  "igst_amount": 0.0, "total_tax": 3150.0, "round_off": 0.0,
  "grand_total": 20650.0, "amount_due": 20650.0
}
```

Error examples: `409 INVOICE_NOT_EDITABLE` (edit non-draft), `409 INVOICE_HAS_PAYMENTS`
(cancel with payments), `400 GSTIN_INVALID`.

---

## 9.5 Collections

| Method | Path | Description |
| --- | --- | --- |
| GET | `/collections/overdue` | List overdue invoices (sorted by amount/days) |
| POST | `/collections/reminders` | Send reminder for one invoice |
| POST | `/collections/reminders/bulk:preview` | Preview bulk (count + total) |
| POST | `/collections/reminders/bulk` | Send bulk (after confirm; idempotent) |
| GET | `/collections/dashboard` | Collections summary |

`POST /collections/reminders` request:
```json
{ "invoice_id": "uuid", "channel": "WHATSAPP", "language": "en" }
```
Response `200`: `{ "reminder_id": "uuid", "status": "SENT", "provider_message_id": "wamid..." }`

---

## 9.6 Dashboard

### `GET /dashboard?from=2026-04-01&to=2026-06-30`
```json
{
  "revenue": 845000.00,
  "pending": 230000.00,
  "overdue": 92000.00,
  "aging": [
    { "bucket": "0-30", "invoices": 8, "outstanding": 120000.00 },
    { "bucket": "31-60", "invoices": 3, "outstanding": 70000.00 },
    { "bucket": "61-90", "invoices": 1, "outstanding": 25000.00 },
    { "bucket": "90+",  "invoices": 1, "outstanding": 15000.00 }
  ],
  "cashflow": [
    { "period": "2026-07", "expected_inflow": 180000.00 },
    { "period": "2026-08", "expected_inflow": 95000.00 }
  ],
  "top_customers": [ { "customer_id": "uuid", "name": "ABC Traders", "revenue": 210000.0 } ]
}
```

---

## 9.7 AI Copilot

### `POST /ai/chat`
Request:
```json
{ "message": "Invoice ABC Traders for 50 bags cement at 350, 18% gst",
  "session_id": "uuid-or-null", "channel": "web" }
```
Response `200` (needs confirmation):
```json
{
  "session_id": "uuid",
  "intent": "create_invoice",
  "message": "I'll create an invoice for ABC Traders — 50 BAG cement @ ₹350, 18% GST. Grand total ₹20,650. Confirm?",
  "requires_confirmation": true,
  "pending_action": { "type": "create_invoice", "preview": { /* invoice draft */ } },
  "data": null,
  "suggested_actions": [ { "label": "Confirm", "value": "yes" }, { "label": "Cancel", "value": "no" } ]
}
```
Response `200` (read intent, no confirmation):
```json
{
  "session_id": "uuid",
  "intent": "list_unpaid_invoices",
  "message": "You have 12 unpaid invoices totalling ₹2,30,000.",
  "requires_confirmation": false,
  "data": { "invoices": [ /* ... */ ], "total": 230000.0 },
  "suggested_actions": [ { "label": "Send reminders", "value": "send reminders to all overdue" } ]
}
```

Guardrails: input sanitised; LLM output validated against the response schema; any
money/GST figures recomputed server-side from authoritative data. See Doc 10 & 12.

### `GET /ai/sessions/{id}` → conversation history (last N turns).

---

## 9.8 Webhooks

### `POST /webhooks/whatsapp` (inbound messages + delivery status)
- `GET` variant handles Meta's verification challenge (`hub.challenge`).
- `POST` verifies `X-Hub-Signature-256` HMAC; inbound text is routed into `/ai/chat`
  pipeline keyed by the sender's phone → resolved tenant.

---

## 9.9 Health

| Path | Purpose |
| --- | --- |
| `GET /health` | liveness (always 200 if process up) |
| `GET /health/ready` | readiness (checks DB + critical deps) |

---

## 9.10 OpenAPI

FastAPI serves the full schema at `/api/v1/openapi.json` and interactive docs at `/docs`
(Swagger) and `/redoc`. The frontend generates types from this schema.
