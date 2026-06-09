#!/usr/bin/env bash
# Verify Hostinger DNS points to Azure before binding custom domains.
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

echo "Checking DNS for KuberAIQ → Azure..."
echo ""

check_cname() {
  local name="$1"
  local expected="$2"
  local result
  result=$(dig +short "$name" CNAME 2>/dev/null | sed 's/\.$//' | head -1)
  if [[ "$result" == "${expected}." ]] || [[ "$result" == "$expected" ]]; then
    echo "  OK  $name → $result"
    return 0
  fi
  local a_record
  a_record=$(dig +short "$name" A 2>/dev/null | head -1)
  echo "  FAIL $name"
  echo "       Expected CNAME: $expected"
  echo "       Got CNAME: ${result:-none}  A: ${a_record:-none}"
  return 1
}

OK=true
check_cname "$WEB_DOMAIN" "$WEB_TARGET" || OK=false
check_cname "$API_DOMAIN" "$API_TARGET" || OK=false

echo ""
if [[ "$OK" == "true" ]]; then
  echo "DNS CNAMEs look good."
  if curl -sf --max-time 8 "${PUBLIC_API_URL}/health" >/dev/null 2>&1; then
    echo "  HTTPS API: ${PUBLIC_API_URL}/health — reachable"
  else
    echo "  HTTPS API not yet reachable (SSL bind may be pending). Run setup-kuberaiq-domains.sh"
  fi
  if curl -sf --max-time 8 "${PUBLIC_WEB_URL}" >/dev/null 2>&1; then
    echo "  HTTPS web: ${PUBLIC_WEB_URL} — reachable"
  else
    echo "  HTTPS web not yet reachable. Run: ./scripts/setup-kuberaiq-domains.sh"
  fi
  echo ""
  echo "Next: ./scripts/setup-kuberaiq-domains.sh"
else
  echo "Update Hostinger DNS (see ./scripts/setup-kuberaiq-domains.sh for exact records),"
  echo "wait 15–30 min, then re-run this script."
fi
