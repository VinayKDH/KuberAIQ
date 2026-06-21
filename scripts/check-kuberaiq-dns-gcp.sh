#!/usr/bin/env bash
# Verify Hostinger DNS points to GCP Cloud Run (not disabled Azure App Services).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/.env.gcp}"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

WEB_DOMAIN="${PUBLIC_WEB_DOMAIN:-www.kuberaiq.com}"
API_DOMAIN="${PUBLIC_API_DOMAIN:-api.kuberaiq.com}"
PUBLIC_WEB_URL="${PUBLIC_WEB_URL:-https://${WEB_DOMAIN}}"
PUBLIC_API_URL="${PUBLIC_API_URL:-https://${API_DOMAIN}}"
GCP_WEB_FALLBACK="${GCP_WEB_ORIGIN:-https://kuberaiq-web-gcp-zu3hk22ncq-el.a.run.app}"
GCP_API_FALLBACK="${GCP_API_ORIGIN:-https://kuberaiq-api-gcp-zu3hk22ncq-el.a.run.app}"

AZURE_WEB="kuberaiq-web-prod.azurewebsites.net"
AZURE_API="kuberaiq-api-prod.azurewebsites.net"
GCP_CNAME="ghs.googlehosted.com"

echo "Checking DNS for KuberAIQ → GCP Cloud Run..."
echo ""

check_cname() {
  local name="$1"
  local result
  result=$(dig +short "$name" CNAME 2>/dev/null | sed 's/\.$//' | head -1)
  if [[ "$result" == "${GCP_CNAME}" ]] || [[ "$result" == "${GCP_CNAME}." ]]; then
    echo "  OK  $name → $result (GCP)"
    return 0
  fi
  if [[ "$result" == *"azurewebsites.net"* ]]; then
    echo "  FAIL $name → $result (Azure — Site Disabled 403)"
    echo "       Update Hostinger CNAME to: $GCP_CNAME"
    echo "       Then run: ./scripts/setup-gcp-domains.sh"
    return 1
  fi
  local a_record
  a_record=$(dig +short "$name" A 2>/dev/null | head -1)
  echo "  WARN $name"
  echo "       CNAME: ${result:-none}  A: ${a_record:-none}"
  echo "       Expected CNAME: $GCP_CNAME"
  return 1
}

OK=true
check_cname "$WEB_DOMAIN" || OK=false
check_cname "$API_DOMAIN" || OK=false

echo ""
if curl -sf --max-time 8 "${PUBLIC_WEB_URL}" 2>/dev/null | head -c 200 | grep -qi "site disabled"; then
  echo "  FAIL ${PUBLIC_WEB_URL} — Azure 'Site Disabled' (DNS still points to Azure)"
  OK=false
elif curl -sf --max-time 8 "${PUBLIC_WEB_URL}" >/dev/null 2>&1; then
  echo "  OK  ${PUBLIC_WEB_URL} — reachable"
else
  echo "  PENDING ${PUBLIC_WEB_URL} — not yet reachable (DNS/SSL propagation or mapping pending)"
fi

if curl -sf --max-time 8 "${PUBLIC_API_URL}/health" >/dev/null 2>&1; then
  echo "  OK  ${PUBLIC_API_URL}/health — reachable"
elif curl -sf --max-time 8 "${PUBLIC_API_URL}/health" 2>&1 | grep -qi "site disabled"; then
  echo "  FAIL ${PUBLIC_API_URL} — Azure 'Site Disabled'"
  OK=false
else
  echo "  PENDING ${PUBLIC_API_URL}/health — not yet reachable"
fi

echo ""
if [[ "$OK" != "true" ]]; then
  echo "Use Cloud Run URLs until DNS is fixed:"
  echo "  Web: $GCP_WEB_FALLBACK"
  echo "  API: $GCP_API_FALLBACK"
  exit 1
fi

echo "Custom domains look good. Run ./scripts/setup-gcp-domains.sh if mappings are not yet created."
