# 12. Security Design

Security is layered: edge (WAF) → transport (TLS) → identity (Entra/JWT) →
authorization (RBAC + tenant isolation) → application (validation, rate limits) →
AI (prompt-injection guardrails) → data (encryption, audit) → ops (secrets, monitoring).

## 12.1 Authentication

- **Users:** Microsoft Entra ID via OIDC (authorization code + PKCE). The backend
  validates the Entra `id_token` (issuer, audience, signature via JWKS, expiry, nonce).
- **App tokens:** On first login the backend mints its own JWTs:
  - Access token: 15 min, signed RS256, claims `{sub, company_id, role, jti}`.
  - Refresh token: 7 days, **rotating**, stored hashed; reuse detection revokes the family.
- Tokens delivered to the web app as `httpOnly`, `Secure`, `SameSite=Strict` cookies.
- **Local dev:** `USE_MOCK_AUTH=true` issues a dev JWT for a seeded owner.

## 12.2 Authorization (RBAC + tenancy)

| Role | Capabilities |
| --- | --- |
| OWNER | Full access incl. delete customer, cancel invoice, bulk reminders, settings |
| STAFF | Create/edit invoices & customers, record payments, send single reminders |
| VIEWER | Read-only (dashboard, lists, PDFs) |

- Enforced server-side via a `require_role(...)` dependency on every route.
- **Tenant isolation:** every query filters by `company_id` from the token; objects from
  other tenants return `404`. A defensive check in the repository base prevents
  cross-tenant access even if a service forgets.

## 12.3 Input validation

- All request bodies validated by Pydantic v2 schemas (types, ranges, regex).
- Domain value objects re-validate invariants (GSTIN checksum, phone format, money ≥ 0).
- Strict allow-lists for enums (status, channel, method, GST rate).
- File/Blob access only through signed, short-lived SAS URLs scoped to the tenant's path.

## 12.4 Rate limiting & abuse protection

| Scope | Limit (default) |
| --- | --- |
| Per IP (global) | 100 req/min |
| Per user | 300 req/min |
| `/auth/*` | 10 req/min per IP |
| `/ai/chat` | 20 req/min per user + per-tenant token budget |
| Bulk reminders | confirmation required + per-customer 48h cooldown |

Implemented via middleware (Redis token bucket in prod; in-memory for local) plus
Front Door WAF rate rules. `429` responses include `Retry-After`.

## 12.5 AI / prompt-injection protection

(Full detail in Doc 10.5.) Key controls:

1. **Untrusted-data framing** — user and customer text is data, never instructions.
2. **Tool allow-listing** — the model can only invoke registered, typed tools.
3. **No money from the model** — GST/totals computed deterministically in the domain;
   output guardrail recomputes and rejects mismatches.
4. **Entity grounding** — customers/invoices resolved via DB lookups; no fabricated IDs.
5. **Output schema validation** — responses must match the JSON schema or fall back safely.
6. **Confirm-before-commit** — all writes pass the human-in-the-loop interrupt gate.
7. **Content filtering** — Azure OpenAI content filters enabled; injection-pattern denylist.

## 12.6 OWASP Top 10 (2021) mapping

| Risk | Mitigation |
| --- | --- |
| A01 Broken Access Control | RBAC + `company_id` tenant scoping + repo-level guard; deny-by-default |
| A02 Cryptographic Failures | TLS 1.2+, RS256 JWT, encryption at rest, secrets in Key Vault |
| A03 Injection | Pydantic validation, SQLAlchemy parameterised queries (no raw SQL concat), prompt-injection guardrails |
| A04 Insecure Design | Threat model, confirm-before-commit, least privilege, idempotency |
| A05 Security Misconfiguration | Hardened headers, no debug in prod, private endpoints, IaC reviewed |
| A06 Vulnerable Components | Dependabot/`pip-audit`/`npm audit`, image scanning in CI |
| A07 Auth Failures | Entra OIDC, short-lived rotating tokens, reuse detection, rate-limited auth |
| A08 Software/Data Integrity | Signed images, pinned deps, SBOM, protected branches |
| A09 Logging/Monitoring Failures | Structured logs, audit trail, alerts, App Insights |
| A10 SSRF | No user-controlled outbound URLs; egress allow-list; webhook signature checks |

## 12.7 Security headers & CORS

- `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, `Content-Security-Policy` (strict), `Referrer-Policy`.
- CORS allow-list = known frontend origins only; credentials enabled; no wildcard.

## 12.8 Secrets management

- All secrets (DB creds, JWT keys, WhatsApp tokens, OpenAI keys) in **Azure Key Vault**.
- Apps read secrets via **Managed Identity** (no keys in app settings or images).
- Local dev uses `.env` (git-ignored). CI uses GitHub OIDC → Azure (no long-lived creds).
- JWT signing keys rotated; key IDs (`kid`) support rolling rotation.

## 12.9 Audit & data protection

- Append-only `audit_logs` for every create/update/cancel/send/payment with before/after,
  actor, IP, timestamp.
- PII (phone, GSTIN, address) access is logged; retention & deletion policy: customer
  data purged 90 days after account closure; invoices retained per statutory GST period.
- Right-to-deletion supported via soft-delete + scheduled hard-purge job.

## 12.10 Threat model summary (STRIDE, abbreviated)

| Threat | Example | Control |
| --- | --- | --- |
| Spoofing | Forged WhatsApp webhook | HMAC signature verification |
| Tampering | Client alters invoice total | Server recomputes; ignores client totals |
| Repudiation | "I didn't send that reminder" | Audit logs with actor + provider message id |
| Info disclosure | Cross-tenant read | Tenant scoping + repo guard + 404 |
| DoS | Flood `/ai/chat` | Rate limits + token budgets + WAF |
| Elevation | STAFF cancels invoice | `require_role(OWNER)` on cancel |
