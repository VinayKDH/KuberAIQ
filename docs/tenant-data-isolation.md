# Tenant data isolation

This document explains how KuberAIQ isolates customer (tenant) data today, what platform administrators can access, and options for stronger isolation on the roadmap.

## Current architecture

KuberAIQ runs as a **multi-tenant SaaS application** on a **single PostgreSQL database** (GCP Cloud SQL in production). Each MSME business is a **company** row; operational data (invoices, customers, products, payments, compliance records, AI sessions, and so on) is scoped by **`company_id`**.

```
┌─────────────────────────────────────────────────────────┐
│  PostgreSQL (single instance)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ company A   │  │ company B   │  │ company C   │      │
│  │ invoices…   │  │ invoices…   │  │ invoices…   │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────┘
```

**There is not a separate database per tenant today.** Isolation is enforced in application code:

- JWT access tokens carry `company_id` for MSME users.
- API dependencies (`get_tenant_context`, `get_verified_auth_context`) reject requests when the token’s `company_id` does not match the user’s assigned company.
- Repositories filter queries by `company_id` (for example invoices, customers, products).
- Chartered accountants (CA role) access client data only through explicit **CA–client assignments**; switching client context is verified server-side.

This is **row-level isolation**, not physical separation.

## What platform admin can and cannot see

The **admin portal** (`/admin/*`) is protected by a server-side **admin API key** (`ADMIN_API_KEY`). It is intended for KuberAIQ operators, not tenant owners.

| Admin can see | Admin cannot see (by default) |
|---------------|-------------------------------|
| Company list: legal name, GSTIN, segment, active/suspended status | Full invoice PDFs or line-item detail in bulk export |
| User emails, roles, active status per tenant | Tenant passwords (OAuth-only in production; no passwords stored) |
| Subscription status and plan code | Raw payment card or UPI credentials |
| Aggregate metrics: invoice counts, AI token usage, compliance overdue counts | Arbitrary cross-tenant business data without using admin APIs |
| Recent invoice metadata (number, status, total, date) for support | WhatsApp message bodies at scale without audit tooling |
| Suspend / activate tenant | Impersonate a tenant user without a separate feature |

Admin APIs are **cross-tenant by design** for operations and support. Access should be limited to a small set of trusted operators, with key rotation and audit logging.

Tenant users (OWNER, STAFF, VIEWER) see **only their company** unless they are a CA with an active assignment to another company.

## Data residency and backups

Production data is stored in **GCP Cloud SQL (asia-south1)**. Backups and restore procedures follow the Cloud SQL retention policy configured for the project. Invoice PDFs may be stored in Azure Blob when `USE_MOCK_BLOB=false`.

## Roadmap options for stronger isolation

| Option | Description | Typical use |
|--------|-------------|-------------|
| **Column-level encryption** | Encrypt sensitive fields (GSTIN, phone, bank refs) with per-tenant or envelope keys | Reduce blast radius if DB is copied |
| **PostgreSQL schemas per tenant** | One schema per company in the same database | Medium enterprises; simpler than many DBs |
| **Dedicated database per enterprise** | Separate Cloud SQL instance for a large customer | Enterprise contracts, data-processing agreements |
| **SOC 2 / ISO 42001 controls** | Access reviews, logging, change management, AI governance | Customer trust and regulated buyers |

None of these replace the need for correct `company_id` filtering in application code; they add defense in depth.

## Recommendations for ISO 42001 and customer trust

For AI management system alignment (ISO 42001) and MSME customer confidence:

1. **Document this model** in customer-facing privacy/security materials: shared DB, logical isolation by `company_id`, India-region hosting.
2. **Minimize admin access**: use break-glass procedures, MFA for operator accounts, and rotate `ADMIN_API_KEY`.
3. **Audit trail**: retain `audit_logs` for sensitive actions; review admin suspend/activate and demo-reset usage.
4. **AI data**: AI sessions and usage logs are tenant-scoped; disclose retention and that prompts may be processed by Azure OpenAI when live LLM is enabled.
5. **Enterprise tier**: offer dedicated DB or customer-managed keys (CMK) when contracts require it.

## Related configuration

- Production auth: `USE_MOCK_AUTH=false`, OAuth providers in `.env.gcp` — see `.env.gcp.example`.
- Admin portal: `ADMIN_API_KEY` on API and web Cloud Run services only.
