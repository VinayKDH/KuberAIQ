#!/usr/bin/env bash
# Temporary: allow GCP Cloud Run (dynamic egress) to reach Azure Postgres Flexible Server.
# Remove rule allow-gcp-cloudrun-temp when switching back to Azure-only or tightening security.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/.env.prod}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE" >&2
  exit 1
fi

# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a

RG="${AZURE_RESOURCE_GROUP:-rg-kuberaiq-prod}"
SERVER="${AZURE_POSTGRES_SERVER_NAME:-kuberaiq-pg-kggg3t2rwrbwg}"
RULE_NAME="${AZURE_POSTGRES_GCP_RULE_NAME:-allow-gcp-cloudrun-temp}"

echo "==> Adding Postgres firewall rule: $RULE_NAME (0.0.0.0 - 255.255.255.255)"
az postgres flexible-server firewall-rule create \
  --resource-group "$RG" \
  --name "$SERVER" \
  --rule-name "$RULE_NAME" \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 255.255.255.255

echo "==> Current firewall rules"
az postgres flexible-server firewall-rule list \
  --resource-group "$RG" \
  --name "$SERVER" \
  -o table

echo ""
echo "Done. Retry GCP mock-login /health/ready after ~1 minute."
