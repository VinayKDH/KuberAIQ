# Monitoring Strategy — VyaparAI

This document describes the observability stack for VyaparAI on Azure. It complements
[docs/11-azure-architecture.md](../docs/11-azure-architecture.md) §11.5–11.6.

## Goals

- Detect outages and SLO breaches before users report them.
- Correlate API, frontend, database, and external dependency failures.
- Track AI cost and latency per tenant without logging PII.

## Stack

| Component | Purpose |
| --- | --- |
| **Application Insights** | Distributed tracing, request/dependency telemetry, exceptions, custom metrics |
| **Log Analytics Workspace** | Central log store; KQL queries, dashboards, alert rules |
| **Azure Monitor Alerts** | Threshold and anomaly alerts routed to Action Groups |
| **Synthetic availability tests** | Multi-region HTTP probes against `/health/ready` |

Both App Services (API + Web) are wired to Application Insights via the
`APPLICATIONINSIGHTS_CONNECTION_STRING` app setting (see `infra/bicep/main.bicep`).

## Golden signals

Monitor the four golden signals per service:

1. **Latency** — p50 / p95 / p99 request duration (API and frontend page loads).
2. **Traffic** — requests per minute, active tenants, WhatsApp webhook volume.
3. **Errors** — HTTP 5xx rate, unhandled exceptions, failed dependency calls.
4. **Saturation** — App Service CPU/memory, PostgreSQL CPU/connections/storage, OpenAI TPM.

## Key dashboards

Create an Azure Dashboard (or Workbook) with:

- API request rate, error rate, and latency percentiles.
- Dependency health: PostgreSQL, Blob Storage, Azure OpenAI, WhatsApp Cloud API.
- LLM tokens consumed and estimated cost per `company_id` (custom metric).
- Frontend Core Web Vitals (if using App Insights browser SDK).
- Database: CPU %, active connections, storage used, replication lag (prod).

## Structured logging

- Backend emits **JSON logs** via structlog with fields: `request_id`, `company_id`,
  `user_id`, `level`, `event`, `duration_ms`.
- **Never log** secrets, JWTs, full GSTIN/phone numbers, or invoice line details.
- Log level: `DEBUG` (dev), `INFO` (staging/prod), `WARNING` for deprecations.

Correlation: propagate `X-Request-ID` from the edge through API → DB → external calls.

## Alert rules (recommended)

Route all alerts to an **Action Group** (email + Microsoft Teams + PagerDuty/on-call).

| Alert | Condition | Severity | Window |
| --- | --- | --- | --- |
| High API error rate | HTTP 5xx > 2% of requests | Sev 1 | 5 min |
| API latency SLO breach | p95 > 2 s | Sev 2 | 10 min |
| API unavailable | Synthetic test failure × 2 regions | Sev 1 | 5 min |
| DB CPU high | PostgreSQL CPU > 80% | Sev 2 | 15 min |
| DB connections high | Active connections > 80% of max | Sev 2 | 10 min |
| DB storage low | Free storage < 15% | Sev 3 | 1 h |
| OpenAI failures | Dependency failure rate > 5% | Sev 2 | 5 min |
| WhatsApp failures | Webhook processing errors > 10/min | Sev 2 | 5 min |
| App Service memory | Available memory < 20% | Sev 3 | 15 min |

## Synthetic monitoring

Configure **Standard Web Tests** in Application Insights:

- **API readiness**: `GET https://<api-app>.azurewebsites.net/health/ready` every 5 min
  from Central India + South India.
- **Frontend availability**: `GET https://<web-app>.azurewebsites.net/` every 5 min.

Alert when two consecutive failures occur from any location.

## On-call runbooks

For each alert, maintain a runbook link in the Action Group notification:

1. Check App Insights **Failures** blade for spike correlation.
2. Verify PostgreSQL metrics and recent deployments.
3. Check Azure Status and WhatsApp/OpenAI status pages.
4. Roll back via redeploying previous container tag if a bad release is suspected.

## Retention

| Data | Retention |
| --- | --- |
| App Insights telemetry (hot) | 90 days |
| Log Analytics | 30 days (configurable in Bicep) |
| Audit logs (Postgres + LA mirror) | 1 year |
| Archived logs (Blob, compliance) | 1 year |

## Local development

Docker Compose does not ship Application Insights. Use structured console logs locally.
Enable App Insights in staging/prod only.
