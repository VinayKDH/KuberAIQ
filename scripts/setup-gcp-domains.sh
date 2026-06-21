#!/usr/bin/env bash
# Map www.kuberaiq.com + api.kuberaiq.com to GCP Cloud Run services.
#
# Prerequisite: update Hostinger DNS to the records printed below, wait 5–30 min.
# Azure App Services are disabled — DNS still points there, causing "Site Disabled" 403.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/.env.gcp}"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_REGION:-asia-south1}"
WEB_SERVICE="${GCP_WEB_SERVICE:-kuberaiq-web-gcp}"
API_SERVICE="${GCP_API_SERVICE:-kuberaiq-api-gcp}"
WEB_DOMAIN="${PUBLIC_WEB_DOMAIN:-www.kuberaiq.com}"
API_DOMAIN="${PUBLIC_API_DOMAIN:-api.kuberaiq.com}"
APEX_DOMAIN="${PUBLIC_APEX_DOMAIN:-kuberaiq.com}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "Set GCP_PROJECT_ID or configure gcloud default project." >&2
  exit 1
fi

map_domain() {
  local service="$1"
  local domain="$2"
  if gcloud beta run domain-mappings describe "$domain" --region "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1; then
    echo "  OK  $domain already mapped to $service"
  else
    echo "  ==> Mapping $domain → $service"
    gcloud beta run domain-mappings create \
      --service "$service" \
      --domain "$domain" \
      --region "$REGION" \
      --project "$PROJECT_ID"
  fi
}

echo "=========================================="
echo " GCP Cloud Run custom domains — KuberAIQ"
echo "=========================================="
echo ""
echo "Project:  $PROJECT_ID"
echo "Region:   $REGION"
echo "Web svc:  $WEB_SERVICE"
echo "API svc:  $API_SERVICE"
echo ""
echo "Hostinger DNS (replace Azure CNAMEs):"
echo "  Type: CNAME | Name: www | Value: ghs.googlehosted.com"
echo "  Type: CNAME | Name: api | Value: ghs.googlehosted.com"
echo ""
echo "Apex redirect (Hostinger → Redirects):"
echo "  ${APEX_DOMAIN}  →  https://${WEB_DOMAIN}"
echo ""
echo "After updating DNS, run this script to create Cloud Run domain mappings."
echo "Google may require additional TXT/CNAME records — gcloud output will list them."
echo ""

map_domain "$WEB_SERVICE" "$WEB_DOMAIN"
map_domain "$API_SERVICE" "$API_DOMAIN"

echo ""
echo "Domain mapping status:"
gcloud beta run domain-mappings list --region "$REGION" --project "$PROJECT_ID" 2>/dev/null || true

echo ""
echo "Verify DNS: ENV_FILE=$ENV_FILE ./scripts/check-kuberaiq-dns-gcp.sh"
echo ""
echo "After DNS + SSL propagate, update .env.gcp:"
echo "  NEXT_PUBLIC_WEB_URL=https://${WEB_DOMAIN}"
echo "  GOOGLE_REDIRECT_URI=https://${WEB_DOMAIN}/auth/callback"
echo "Then redeploy: ENV_FILE=$ENV_FILE ./scripts/deploy-gcp.sh"
