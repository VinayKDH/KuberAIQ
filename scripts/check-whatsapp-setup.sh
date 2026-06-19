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
VERIFY_CHALLENGE="kuberaiq-verify-$(date +%s)"

echo "=== KuberAIQ WhatsApp setup check ==="
echo "API base: $API_BASE"
echo "Webhook URL: $WEBHOOK_URL"
echo "ENV file: $ENV_FILE"
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

if [[ "${USE_MOCK_WHATSAPP:-}" == "false" ]]; then
  echo "✓ USE_MOCK_WHATSAPP=false (live mode requested)"
elif [[ "$missing" -eq 0 ]]; then
  echo "ℹ USE_MOCK_WHATSAPP not false — deploy may still enable live when creds are present"
else
  echo "ℹ USE_MOCK_WHATSAPP unset — mock notifier will be used without creds"
fi

echo ""
echo "Health integrations:"
health_json="$(curl -fsS "${API_BASE}/health/integrations" 2>/dev/null || true)"
if [[ -n "$health_json" ]]; then
  echo "$health_json" | python3 -m json.tool 2>/dev/null || echo "$health_json"
  whatsapp_mode="$(echo "$health_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('whatsapp_mode','?'))" 2>/dev/null || echo "?")"
  echo ""
  echo "whatsapp_mode: $whatsapp_mode"
else
  echo "✗ Could not reach ${API_BASE}/health/integrations"
  missing=1
fi

if [[ -n "${WHATSAPP_VERIFY_TOKEN:-}" ]]; then
  echo ""
  echo "Webhook verify probe (GET):"
  verify_resp="$(curl -fsS -G "$WEBHOOK_URL" \
    --data-urlencode "hub.mode=subscribe" \
    --data-urlencode "hub.verify_token=${WHATSAPP_VERIFY_TOKEN}" \
    --data-urlencode "hub.challenge=${VERIFY_CHALLENGE}" 2>/dev/null || true)"
  if [[ "$verify_resp" == "$VERIFY_CHALLENGE" ]]; then
    echo "✓ Webhook verification endpoint returned challenge"
  else
    echo "✗ Webhook verify failed (expected challenge echo)"
    missing=1
  fi
fi

echo ""
echo "Meta Developer Console (WhatsApp → Configuration):"
echo "  1. Callback URL: $WEBHOOK_URL"
echo "  2. Verify token: \${WHATSAPP_VERIFY_TOKEN} (same value in $ENV_FILE)"
echo "  3. Subscribe to: messages (and message status if available)"
echo "  4. Approved templates: payment_reminder_en, payment_reminder_hi (body {{1}})"
echo "  5. Set WHATSAPP_PHONE_NUMBER_ID + WHATSAPP_ACCESS_TOKEN in $ENV_FILE"
echo "  6. Owner links mobile: Settings → Integrations → WhatsApp AI copilot"
echo "  7. Set USE_MOCK_WHATSAPP=false for production live sends"
echo "  8. Redeploy: ENV_FILE=$ENV_FILE ./scripts/deploy-gcp.sh"
echo "  9. Docs: docs/whatsapp-production.md"
echo ""

if [[ "$missing" -eq 1 ]]; then
  exit 1
fi
