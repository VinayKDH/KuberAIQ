#!/usr/bin/env bash
# Verify Razorpay billing configuration for KuberAIQ (test or live).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/.env.prod}"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  set -a && source "$ENV_FILE" && set +a
fi

API_BASE="${API_BASE:-https://api.kuberaiq.com}"
WEBHOOK_URL="${API_BASE}/api/v1/billing/webhooks/razorpay"

echo "=== KuberAIQ Razorpay setup check ==="
echo "API base: $API_BASE"
echo ""

missing=0
for var in RAZORPAY_KEY_ID RAZORPAY_KEY_SECRET; do
  if [[ -z "${!var:-}" ]]; then
    echo "✗ $var is not set"
    missing=1
  else
    echo "✓ $var is set"
  fi
done

if [[ -z "${RAZORPAY_WEBHOOK_SECRET:-}" ]]; then
  echo "⚠ RAZORPAY_WEBHOOK_SECRET is empty — checkout still works via browser verify; webhooks will be rejected"
else
  echo "✓ RAZORPAY_WEBHOOK_SECRET is set"
fi

echo ""
echo "Health integrations:"
curl -fsS "${API_BASE}/health/integrations" | python3 -m json.tool 2>/dev/null || curl -fsS "${API_BASE}/health/integrations"
echo ""

echo "Razorpay Dashboard (Test mode):"
echo "  1. Settings → Webhooks → Add New Webhook"
echo "  2. URL: $WEBHOOK_URL"
echo "  3. Events: payment.captured"
echo "  4. Copy signing secret → RAZORPAY_WEBHOOK_SECRET in $ENV_FILE"
echo "  5. Redeploy API: ENV_FILE=$ENV_FILE ./scripts/deploy-prod.sh"
echo ""

if [[ "$missing" -eq 1 ]]; then
  exit 1
fi
