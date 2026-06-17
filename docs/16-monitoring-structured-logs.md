# Structured Logging Baseline

KuberAIQ backend logs should include these fields for alerting and dashboarding:

- `event`: stable event name (`scheduled_reminders_completed`, `whatsapp_message_sent`, etc.)
- `request_id`: request correlation id from middleware
- `company_id`: tenant scope for multi-tenant traces
- `user_id`: actor when available
- `route`: API route or AI route bucket
- `status`: success/failure outcome
- `duration_ms`: processing time
- `error`: sanitized message when failures occur

## Suggested Alert Conditions

- High `error` rate (>5%) for payment and invoice endpoints.
- Zero successful scheduler runs in 24h.
- AI token usage crossing monthly soft cap thresholds by tenant.
