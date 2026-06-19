# WhatsApp production readiness (KuberAIQ)

## Environment variables

| Variable | Required for live | Purpose |
|----------|-------------------|---------|
| `USE_MOCK_WHATSAPP` | No (default mock) | Set `false` for live Graph API sends |
| `WHATSAPP_PHONE_NUMBER_ID` | Yes (live) | Meta phone number ID |
| `WHATSAPP_ACCESS_TOKEN` | Yes (live) | Permanent or long-lived system user token |
| `WHATSAPP_VERIFY_TOKEN` | Yes (webhook) | Arbitrary string; must match Meta Console |
| `WHATSAPP_APP_SECRET` | Yes (prod inbound) | HMAC validation for `POST /api/v1/webhooks/whatsapp` |

Mock mode stays active when phone ID or access token are missing — no Meta secrets required for dev/demo.

## Webhook

- **URL:** `https://api.kuberaiq.com/api/v1/webhooks/whatsapp`
- **Verify:** `GET` with `hub.mode=subscribe`, `hub.verify_token`, `hub.challenge`
- **Inbound:** `POST` with `X-Hub-Signature-256` when `WHATSAPP_APP_SECRET` is set

## Meta templates

Register utility templates with a single body parameter `{{1}}` (full reminder text):

- `payment_reminder_en` — English payment reminders
- `payment_reminder_hi` — Hindi payment reminders
- `invoice_share` — invoice share (optional)
- `compliance_reminder` — compliance alerts (optional)

Reminder copy is built in `WHATSAPP_REMINDER_BODY` (`backend/app/core/constants.py`) and respects `default_reminder_language` on the company.

## Owner copilot

1. Deploy with live WhatsApp creds (`USE_MOCK_WHATSAPP=false`).
2. Owner links mobile: **Settings → Integrations → WhatsApp AI copilot**.
3. Message the business number from that phone within the 24h customer service window.

## Verification

```bash
ENV_FILE=.env.prod ./scripts/check-whatsapp-setup.sh
```

Checks env vars, `/health/integrations` (`whatsapp_mode`, `whatsapp_configured`), and prints Meta Console steps.
