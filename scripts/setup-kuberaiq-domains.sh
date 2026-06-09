#!/usr/bin/env bash
# Bind www.kuberaiq.com + api.kuberaiq.com to Azure App Services and issue managed SSL.
#
# Prerequisite: add DNS records in Hostinger (see output below), wait 5–30 min propagation.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../infra/azure/naming.sh
source "$ROOT/infra/azure/naming.sh"
ENV_FILE="${ENV_FILE:-$ROOT/.env.prod}"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

RG="${AZURE_RESOURCE_GROUP:-$KUBERAIQ_RG_PROD}"
WEB_APP="${AZURE_WEB_APP_NAME:-$KUBERAIQ_WEB_APP_PROD}"
API_APP="${AZURE_API_APP_NAME:-$KUBERAIQ_API_APP_PROD}"
WEB_HOST="${AZURE_WEB_HOSTNAME:-${KUBERAIQ_WEB_APP_PROD}.azurewebsites.net}"
API_HOST="${AZURE_API_HOSTNAME:-${KUBERAIQ_API_APP_PROD}.azurewebsites.net}"

WEB_DOMAIN="${PUBLIC_WEB_DOMAIN:-www.kuberaiq.com}"
API_DOMAIN="${PUBLIC_API_DOMAIN:-api.kuberaiq.com}"
APEX_DOMAIN="${PUBLIC_APEX_DOMAIN:-kuberaiq.com}"
PUBLIC_WEB_URL="${PUBLIC_WEB_URL:-https://${WEB_DOMAIN}}"
PUBLIC_API_URL="${PUBLIC_API_URL:-https://${API_DOMAIN}}"

WEB_VERIFY=$(az webapp show --resource-group "$RG" --name "$WEB_APP" --query customDomainVerificationId -o tsv)
API_VERIFY=$(az webapp show --resource-group "$RG" --name "$API_APP" --query customDomainVerificationId -o tsv)

echo "=========================================="
echo " Hostinger DNS records for KuberAIQ"
echo "=========================================="
echo ""
echo "1) Website + Webapp (Next.js — landing, login, dashboard):"
echo "   Type: CNAME | Name: www | Value: ${WEB_HOST}"
echo ""
echo "2) API backend:"
echo "   Type: CNAME | Name: api | Value: ${API_HOST}"
echo ""
echo "3) Apex redirect (recommended — Hostinger → Redirects):"
echo "   ${APEX_DOMAIN}  →  https://${WEB_DOMAIN}"
echo ""
echo "4) Azure domain verification (TXT — add if SSL bind fails):"
echo "   Type: TXT | Name: asuid.www | Value: ${WEB_VERIFY}"
echo "   Type: TXT | Name: asuid.api  | Value: ${API_VERIFY}"
echo ""
echo "After DNS propagates, this script binds hostnames + free managed certificates."
echo ""

bind_hostname() {
  local app="$1"
  local hostname="$2"
  if az webapp config hostname list --resource-group "$RG" --webapp-name "$app" -o tsv 2>/dev/null | grep -qx "$hostname"; then
    echo "    $hostname already mapped to $app"
  else
    az webapp config hostname add --resource-group "$RG" --webapp-name "$app" --hostname "$hostname" --output none
    echo "    Added $hostname → $app"
  fi
}

bind_ssl() {
  local app="$1"
  local hostname="$2"
  local cert_name="${hostname//./-}"

  if ! az webapp config ssl show -g "$RG" --certificate-name "$cert_name" -o none 2>/dev/null; then
    if ! az webapp config ssl create -g "$RG" -n "$app" --hostname "$hostname" \
      --certificate-name "$cert_name" -o none 2>/dev/null; then
      echo "    SSL pending for ${hostname} — DNS may not be propagated yet. Retry in 15–30 min."
      return 1
    fi
    echo "    Managed certificate requested for ${hostname} (provisioning may take a few minutes)"
    sleep 15
  fi

  local thumbprint
  thumbprint=$(az webapp config ssl show -g "$RG" --certificate-name "$cert_name" \
    --query thumbprint -o tsv 2>/dev/null || true)
  if [[ -z "$thumbprint" ]]; then
    echo "    SSL pending for ${hostname} — certificate not ready yet. Re-run this script shortly."
    return 1
  fi

  if az webapp config ssl bind -g "$RG" -n "$app" \
    --certificate-thumbprint "$thumbprint" --ssl-type SNI --hostname "$hostname" \
    --output none 2>/dev/null; then
    echo "    SSL bound: https://${hostname}"
    return 0
  fi
  echo "    SSL pending for ${hostname} — bind failed. Check Azure Portal → TLS/SSL."
  return 1
}

echo "==> Registering custom hostnames in Azure"
bind_hostname "$WEB_APP" "$WEB_DOMAIN"
bind_hostname "$API_APP" "$API_DOMAIN"

echo "==> Binding managed SSL (requires DNS CNAMEs live)"
SSL_OK=true
bind_ssl "$WEB_APP" "$WEB_DOMAIN" || SSL_OK=false
bind_ssl "$API_APP" "$API_DOMAIN" || SSL_OK=false

echo ""
if [[ "$SSL_OK" == "true" ]]; then
  echo "Custom domains are live:"
  echo "  Website + Webapp: ${PUBLIC_WEB_URL}"
  echo "  API:              ${PUBLIC_API_URL}"
  echo "  OAuth redirect:   ${PUBLIC_WEB_URL}/auth/callback"
  echo "  WhatsApp webhook: ${PUBLIC_API_URL}/api/v1/webhooks/whatsapp"
  echo ""
  curl -sf -o /dev/null -w "www HTTP %{http_code}\n" "${PUBLIC_WEB_URL}" || true
  curl -sf -o /dev/null -w "api  HTTP %{http_code}\n" "${PUBLIC_API_URL}/health" || true
  echo ""
  echo "Re-deploy with custom URLs once DNS is stable:"
  echo "  ./scripts/deploy-prod.sh"
  echo "Verify integrations:"
  echo "  ./scripts/verify-track-a.sh"
else
  echo "Hostnames registered in Azure. Complete Hostinger DNS above, then re-run:"
  echo "  ./scripts/setup-kuberaiq-domains.sh"
fi
