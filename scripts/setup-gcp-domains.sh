#!/usr/bin/env bash
# Map www.kuberaiq.com + api.kuberaiq.com to GCP Cloud Run services.
#
# Prerequisites (in order):
#   1. Verify kuberaiq.com in Google Search Console (testkuberqi@gmail.com)
#   2. Update Hostinger DNS — see hostinger_dns_instructions below
#   3. Run this script to create Cloud Run domain mappings
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/.env.gcp}"
DNS_ONLY=false

for arg in "$@"; do
  case "$arg" in
    --dns-only) DNS_ONLY=true ;;
    -h|--help)
      echo "Usage: ENV_FILE=.env.gcp $0 [--dns-only]"
      echo "  --dns-only  Print Hostinger DNS + verification steps; skip gcloud mapping."
      exit 0
      ;;
  esac
done

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
GCP_CNAME_TARGET="${GCP_RUN_CNAME_TARGET:-ghs.googlehosted.com}"
AZURE_WEB_CNAME="${AZURE_WEB_HOSTNAME:-kuberaiq-web-prod.azurewebsites.net}"
AZURE_API_CNAME="${AZURE_API_HOSTNAME:-kuberaiq-api-prod.azurewebsites.net}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "Set GCP_PROJECT_ID or configure gcloud default project." >&2
  exit 1
fi

hostinger_dns_instructions() {
  cat <<EOF
==========================================
 Hostinger DNS — exact records for GCP
==========================================

Sign in: Hostinger → Domains → kuberaiq.com → DNS / DNS Zone

STEP 1 — Domain verification (GCP, one-time)
  Open Google Search Console while logged in as testkuberqi@gmail.com:
    https://search.google.com/search-console/welcome?new_domain_name=${APEX_DOMAIN}
  Choose "Domain" property, verify via DNS TXT at @ (root):
    Type: TXT | Name: @ | Value: <google-site-verification=... from Search Console>
  Or run: gcloud domains verify ${APEX_DOMAIN} --project=${PROJECT_ID}
  Confirm: gcloud domains list-user-verified --project=${PROJECT_ID}

STEP 2 — Replace Azure CNAMEs (required)
  DELETE or EDIT these records if present:
    www  CNAME  ${AZURE_WEB_CNAME}
    api  CNAME  ${AZURE_API_CNAME}

  ADD / CHANGE to:
    Type: CNAME | Name: www | Value: ${GCP_CNAME_TARGET} | TTL: 300 (or default)
    Type: CNAME | Name: api | Value: ${GCP_CNAME_TARGET} | TTL: 300 (or default)

STEP 3 — Remove Azure SSL verification TXT (if present)
    asuid.www  TXT  (any value)
    asuid.api   TXT  (any value)

STEP 4 — Apex redirect (Hostinger → Redirects, not DNS)
    ${APEX_DOMAIN}  →  https://${WEB_DOMAIN}  (301 permanent)

STEP 5 — After this script creates mappings, add any extra records gcloud prints
  (rare — usually the CNAMEs above are enough once domain is verified)

Keep existing mail records (e.g. SPF TXT at @) — do not delete those.

EOF
}

domain_is_verified() {
  gcloud domains list-user-verified --project "$PROJECT_ID" --format="value(id)" 2>/dev/null \
    | grep -Fx "${APEX_DOMAIN}" >/dev/null
}

map_domain() {
  local service="$1"
  local domain="$2"
  if gcloud beta run domain-mappings describe "$domain" --region "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1; then
    echo "  OK  $domain already mapped to $service"
    gcloud beta run domain-mappings describe "$domain" \
      --region "$REGION" --project "$PROJECT_ID" \
      --format="yaml(status.resourceRecords,status.conditions)" 2>/dev/null || true
    return 0
  fi
  echo "  ==> Mapping $domain → $service"
  gcloud beta run domain-mappings create \
    --service "$service" \
    --domain "$domain" \
    --region "$REGION" \
    --project "$PROJECT_ID"
}

echo "=========================================="
echo " GCP Cloud Run custom domains — KuberAIQ"
echo "=========================================="
echo ""
echo "Project:  $PROJECT_ID"
echo "Region:   $REGION"
echo "Web svc:  $WEB_SERVICE  →  ${WEB_DOMAIN}"
echo "API svc:  $API_SERVICE  →  ${API_DOMAIN}"
echo ""

hostinger_dns_instructions

if [[ "$DNS_ONLY" == "true" ]]; then
  echo "(--dns-only: skipping gcloud domain mappings)"
  exit 0
fi

echo "==> Domain verification status"
if domain_is_verified; then
  echo "  OK  ${APEX_DOMAIN} verified for this GCP account"
else
  echo "  FAIL ${APEX_DOMAIN} is NOT verified — Cloud Run mapping will fail."
  echo ""
  echo "  Verify first (Search Console or):"
  echo "    gcloud domains verify ${APEX_DOMAIN} --project=${PROJECT_ID}"
  echo "  Then re-run: ENV_FILE=${ENV_FILE} $0"
  exit 1
fi

echo ""
echo "==> Creating Cloud Run domain mappings"
map_domain "$WEB_SERVICE" "$WEB_DOMAIN"
map_domain "$API_SERVICE" "$API_DOMAIN"

echo ""
echo "Domain mapping status:"
gcloud beta run domain-mappings list --region "$REGION" --project "$PROJECT_ID" 2>/dev/null || true

echo ""
echo "==> Next steps"
echo "  1. Apply Hostinger DNS records above (if not done)"
echo "  2. Wait 5–30 min for DNS + managed SSL"
echo "  3. Verify: ENV_FILE=${ENV_FILE} ./scripts/check-kuberaiq-dns-gcp.sh"
echo "  4. Set in ${ENV_FILE}:"
echo "       PUBLIC_WEB_URL=https://${WEB_DOMAIN}"
echo "       PUBLIC_API_URL=https://${API_DOMAIN}"
echo "       GOOGLE_REDIRECT_URI=https://${WEB_DOMAIN}/auth/callback"
echo "  5. Add OAuth redirect URI in Google Cloud Console (OAuth client):"
echo "       https://${WEB_DOMAIN}/auth/callback"
echo "  6. Redeploy: ENV_FILE=${ENV_FILE} ./scripts/deploy-gcp.sh"
echo ""
echo "See docs/gcp-custom-domains.md for full runbook."
