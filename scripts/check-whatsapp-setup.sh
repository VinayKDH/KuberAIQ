#!/usr/bin/env bash
# Verify WhatsApp Cloud API configuration for KuberAIQ.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/.env.prod}"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  set -a && source "$ENV_FILE" && set +a
fi

API_BASE="${API_BASE:-${PUBLIC_API_URL:-https://api.kuberaiq.com}}"
WEBHOOK_URL="${API_BASE}/api/v1/webhooks/whatsapp"

echo "=== KuberAIQ WhatsApp setup check ==="
echo "API base: $API_BASE"
echo "Webhook URL: $WEBHOOK_URL"
echo ""

missing=0
for var in WHATSAPP_PHONE_NUMBER_ID WHATSAPP_ACCESS_TOKEN; do
  if [[ -z "${!var:-}" ]]; then
    echo "✗ $var is not set"
    missing=1
  else
    echo "✓ $var is set"
  fi
done

if [[ -z "${WHATSAPP_VERIFY_TOKEN:-}" ]]; then
  echo "⚠ WHATSAPP_VERIFY_TOKEN is empty — Meta webhook verification will fail"
else
  echo "✓ WHATSAPP_VERIFY_TOKEN is set"
fi

if [[ -z "${WHATSAPP_APP_SECRET:-}" ]]; then
  echo "⚠ WHATSAPP_APP_SECRET is empty — inbound webhook signature checks are skipped"
else
  echo "✓ WHATSAPP_APP_SECRET is set"
fi

echo ""
echo "Health integrations:"
curl -fsS "${API_BASE}/health/integrations" | python3 -m json.tool 2>/dev/null || curl -fsS "${API_BASE}/health/integrations"
echo ""

echo "Meta Developer Console (WhatsApp → Configuration):"
echo "  1. Callback URL: $WEBHOOK_URL"
echo "  2. Verify token: \${WHATSAPP_VERIFY_TOKEN} (same value in $ENV_FILE)"
echo "  3. Subscribe to: messages (and message status if available)"
echo "  4. Approved templates: payment_reminder_en, payment_reminder_hi (body with {{1}} for message text)"
echo "  5. Set WHATSAPP_PHONE_NUMBER_ID + WHATSAPP_ACCESS_TOKEN in $ENV_FILE"
echo "  6. Owner links mobile: Settings → Integrations → WhatsApp AI copilot"
echo "  7. Set USE_MOCK_WHATSAPP=false (or leave unset — deploy auto-disables mock when creds present)"
echo "  8. Redeploy API: ENV_FILE=$ENV_FILE ./scripts/deploy-prod.sh"
echo ""

if [[ "$missing" -eq 1 ]]; then
  exit 1
fi
