#!/usr/bin/env bash
# Repeatable production QA smoke tests (curl-based).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/.env.prod}"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

API="${PUBLIC_API_URL:-https://api.kuberaiq.com}"
WEB="${PUBLIC_WEB_URL:-https://www.kuberaiq.com}"
APEX="${PUBLIC_APEX_DOMAIN:-kuberaiq.com}"
WHATSAPP_VERIFY_TOKEN="${WHATSAPP_VERIFY_TOKEN:-kuberaiq-verify}"
RAZORPAY_WEBHOOK_SECRET="${RAZORPAY_WEBHOOK_SECRET:-}"

PASS=0
FAIL=0

pass() { echo "  OK   $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL $1"; FAIL=$((FAIL + 1)); }

check_code() {
  local label="$1"
  local expected="$2"
  local actual="$3"
  if [[ "$actual" == "$expected" ]]; then
    pass "$label ($actual)"
  else
    fail "$label (expected $expected, got $actual)"
  fi
}

echo "=== KuberAIQ production QA smoke ==="
echo "API: $API"
echo "Web: $WEB"
echo ""

echo "==> Health"
check_code "GET /health" "200" "$(curl -s -o /dev/null -w '%{http_code}' "$API/health")"
check_code "GET /health/ready" "200" "$(curl -s -o /dev/null -w '%{http_code}' "$API/health/ready")"
check_code "GET /health/integrations" "200" "$(curl -s -o /dev/null -w '%{http_code}' "$API/health/integrations")"
echo ""

echo "==> Auth (unauthenticated)"
check_code "mock-login disabled" "403" "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API/api/v1/auth/mock-login" -H 'Content-Type: application/json' -d '{"email":"qa@example.com"}')"
check_code "billing/status" "401" "$(curl -s -o /dev/null -w '%{http_code}' "$API/api/v1/billing/status")"
check_code "customers" "401" "$(curl -s -o /dev/null -w '%{http_code}' "$API/api/v1/customers")"
check_code "ca/clients" "401" "$(curl -s -o /dev/null -w '%{http_code}' "$API/api/v1/ca/clients")"
check_code "companies/me/advisors" "401" "$(curl -s -o /dev/null -w '%{http_code}' "$API/api/v1/companies/me/advisors")"
echo ""

echo "==> Webhooks"
CH="qa-smoke"
WA=$(curl -sf "$API/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=${WHATSAPP_VERIFY_TOKEN}&hub.challenge=${CH}" 2>/dev/null || echo "")
if [[ "$WA" == "$CH" ]]; then
  pass "WhatsApp verify"
else
  fail "WhatsApp verify"
fi

BODY='{"event":"payment.captured","payload":{"payment":{"entity":{"id":"pay_test"}}}}'
check_code "Razorpay bad signature" "401" "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API/api/v1/billing/webhooks/razorpay" -H 'Content-Type: application/json' -H 'X-Razorpay-Signature: invalid' -d "$BODY")"

if [[ -n "$RAZORPAY_WEBHOOK_SECRET" ]]; then
  SIG=$(printf "%s" "$BODY" | openssl dgst -sha256 -hmac "$RAZORPAY_WEBHOOK_SECRET" | awk '{print $2}')
  check_code "Razorpay valid signature" "204" "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API/api/v1/billing/webhooks/razorpay" -H 'Content-Type: application/json' -H "X-Razorpay-Signature: $SIG" -d "$BODY")"
fi
echo ""

echo "==> Frontend"
for path in / /login /terms /privacy /subscribe; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -L --max-redirs 3 "$WEB$path")
  check_code "GET $path" "200" "$code"
done
echo ""

echo "==> Apex"
if curl -sI --max-time 10 "https://${APEX}" | grep -qi "^location:.*www\\."; then
  pass "Apex redirects to www"
else
  echo "  WARN Apex https://${APEX} does not redirect — client-side guard still applies on www"
fi
echo ""

echo "=========================================="
echo " Results: $PASS passed, $FAIL failed"
echo "=========================================="
if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
