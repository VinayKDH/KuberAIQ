#!/usr/bin/env bash
# Verify Track A production integrations (DNS, API health, auth mode, WhatsApp webhook).
# Optional — run after deploy-prod.sh and setup-kuberaiq-domains.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/.env.prod}"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

WEB_TARGET="${AZURE_WEB_HOSTNAME:-kuberaiq-web-prod.azurewebsites.net}"
API_TARGET="${AZURE_API_HOSTNAME:-kuberaiq-api-prod.azurewebsites.net}"
WEB_DOMAIN="${PUBLIC_WEB_DOMAIN:-www.kuberaiq.com}"
API_DOMAIN="${PUBLIC_API_DOMAIN:-api.kuberaiq.com}"
PUBLIC_WEB_URL="${PUBLIC_WEB_URL:-https://${WEB_DOMAIN}}"
PUBLIC_API_URL="${PUBLIC_API_URL:-https://${API_DOMAIN}}"
WHATSAPP_VERIFY_TOKEN="${WHATSAPP_VERIFY_TOKEN:-kuberaiq-verify}"
USE_MOCK_AUTH="${USE_MOCK_AUTH:-false}"

PASS=0
WARN=0
FAIL=0

pass() { echo "  OK   $1"; PASS=$((PASS + 1)); }
warn() { echo "  WARN $1"; WARN=$((WARN + 1)); }
fail() { echo "  FAIL $1"; FAIL=$((FAIL + 1)); }

check_cname() {
  local name="$1"
  local expected="$2"
  local result
  result=$(dig +short "$name" CNAME 2>/dev/null | sed 's/\.$//' | head -1)
  if [[ "$result" == "${expected}." ]] || [[ "$result" == "$expected" ]]; then
    pass "DNS $name → $result"
    return 0
  fi
  fail "DNS $name (expected CNAME $expected, got ${result:-none})"
  return 1
}

check_http() {
  local url="$1"
  local label="$2"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" || echo "000")
  if [[ "$code" =~ ^[23] ]]; then
    pass "$label HTTP $code ($url)"
  else
    fail "$label HTTP $code ($url)"
  fi
}

echo "=========================================="
echo " KuberAIQ Track A verification"
echo "=========================================="
echo ""

echo "==> DNS (Hostinger → Azure)"
check_cname "$WEB_DOMAIN" "$WEB_TARGET" || true
check_cname "$API_DOMAIN" "$API_TARGET" || true
echo ""

echo "==> API health"
API_URL="$PUBLIC_API_URL"
if ! curl -sf --max-time 10 "${API_URL}/health" >/dev/null 2>&1; then
  API_URL="https://${API_TARGET}"
  warn "Custom API unreachable — falling back to ${API_URL}"
fi

if curl -sf --max-time 10 "${API_URL}/health" | grep -q '"status":"ok"'; then
  pass "Health live (${API_URL}/health)"
else
  fail "Health live (${API_URL}/health)"
fi

if curl -sf --max-time 15 "${API_URL}/health/ready" | grep -q '"database":"ok"'; then
  pass "Health ready (database)"
else
  warn "Health ready check failed (cold start or DB issue)"
fi
echo ""

echo "==> Integration modes"
INTEGRATIONS=$(curl -sf --max-time 10 "${API_URL}/health/integrations" 2>/dev/null || echo "")
if [[ -n "$INTEGRATIONS" ]]; then
  echo "  $INTEGRATIONS"
  if echo "$INTEGRATIONS" | grep -q '"auth_mode":"oauth"'; then
    pass "Auth mode: oauth"
  elif [[ "$USE_MOCK_AUTH" == "true" ]]; then
    warn "Auth mode: mock (expected for pre-OAuth staging)"
  else
    fail "Auth mode: mock (expected oauth in production)"
  fi
  if echo "$INTEGRATIONS" | grep -q '"whatsapp_mode":"live"'; then
    pass "WhatsApp mode: live"
  else
    warn "WhatsApp mode: mock (configure Meta credentials to enable)"
  fi
else
  fail "Could not fetch /health/integrations"
fi
echo ""

echo "==> Auth endpoints"
if [[ "$USE_MOCK_AUTH" == "false" ]]; then
  MOCK_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${API_URL}/api/v1/auth/mock-login" \
    -H "Content-Type: application/json" -d '{"email":"owner@demo.kuberaiq.com"}')
  if [[ "$MOCK_CODE" == "403" ]]; then
    pass "mock-login disabled (403)"
  else
    fail "mock-login should return 403, got $MOCK_CODE"
  fi
else
  warn "Skipping mock-login check (USE_MOCK_AUTH=true)"
fi
echo ""

echo "==> WhatsApp webhook (optional)"
CHALLENGE="verify-$(date +%s)"
WA_RESPONSE=$(curl -sf --max-time 10 \
  "${API_URL}/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=${WHATSAPP_VERIFY_TOKEN}&hub.challenge=${CHALLENGE}" 2>/dev/null || true)
if [[ "$WA_RESPONSE" == "$CHALLENGE" ]]; then
  pass "Webhook verify token accepted"
else
  warn "Webhook verify failed — set WHATSAPP_VERIFY_TOKEN in Meta + .env.prod"
fi
echo ""

echo "==> Web frontend"
check_http "$PUBLIC_WEB_URL" "www" || check_http "https://${WEB_TARGET}" "Azure web"
echo ""

echo "=========================================="
echo " Results: $PASS passed, $WARN warnings, $FAIL failed"
echo "=========================================="
if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
