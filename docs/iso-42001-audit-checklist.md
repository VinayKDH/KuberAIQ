# ISO 42001 Audit Checklist — KuberAIQ Mapping

Use this checklist when preparing for an ISO/IEC 42001-aligned review. Map each control to evidence in the product and `docs/ai-governance.md`.

## A. Context and scope

| Control | KuberAIQ evidence |
| --- | --- |
| A.1 AI system purpose documented | `docs/ai-governance.md` §1 inventory |
| A.2 Interested parties identified | MSME owners, staff, CAs, platform admin |
| A.3 Scope boundaries | Per-tenant SaaS; India MSME billing/compliance |

## B. Governance and roles

| Control | KuberAIQ evidence |
| --- | --- |
| B.1 Roles assigned | OWNER / STAFF / VIEWER / CA / admin — `RBAC_MATRIX` in `constants.py` |
| B.2 Accountability for AI outputs | Owner confirms mutations; audit logs with actor |
| B.3 Admin oversight | Admin portal: tenants, AI usage, audit logs |

## C. Risk management

| Control | KuberAIQ evidence |
| --- | --- |
| C.1 Risk register | `docs/ai-governance.md` §4 |
| C.2 Data minimization | Copilot tools fetch only tenant-scoped aggregates |
| C.3 Fallback when model unavailable | `AzureOpenAiLlm` → `MockLlm`; graceful user message |
| C.4 Cost / abuse controls | Token budget, rate limits, subscription gate |

## D. Lifecycle and operations

| Control | KuberAIQ evidence |
| --- | --- |
| D.1 Environment separation | `ENVIRONMENT` local/dev/staging/production |
| D.2 Integration modes visible | `GET /health/integrations` |
| D.3 Change control for prompts | Versioned prompts in repo; deploy via CI/CD |
| D.4 Incident logging | Structured HTTP + AI interaction logs |

## E. Data and privacy

| Control | KuberAIQ evidence |
| --- | --- |
| E.1 Tenant isolation | `company_id` on all repositories |
| E.2 Consent / terms | Terms & Privacy pages; subscribe flow |
| E.3 Data retention | Postgres backups; audit log retention per ops runbook |

## F. Transparency and explainability

| Control | KuberAIQ evidence |
| --- | --- |
| F.1 User informed of AI use | Assistant UI disclaimer; WhatsApp copilot link message |
| F.2 Confirm before action | Confirm cards in web UI; `requires_confirmation` API |
| F.3 Hindi language support | Reminder templates + MSME UI i18n phase 2 |

## G. Monitoring and improvement

| Control | KuberAIQ evidence |
| --- | --- |
| G.1 Usage metrics | `ai_usage_log`, admin AI usage dashboard |
| G.2 Periodic review | Sprint governance docs update |
| G.3 Customer feedback | support@kuberaiq.com |

## Quick verification commands

```bash
curl -s https://api.kuberaiq.com/health/integrations | jq .
# Expect llm_mode, whatsapp_mode, billing_mode

pytest backend/tests/api/test_rbac.py -q
```
