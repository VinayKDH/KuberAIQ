#!/usr/bin/env bash
# Verify local / dev environment files before deploy-dev.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../infra/azure/naming.sh
source "$ROOT/infra/azure/naming.sh"

ENV_FILE="${ENV_FILE:-$ROOT/.env.dev}"

echo "=== KuberAIQ dev environment check ==="
echo "Env file: $ENV_FILE"
echo "Resource group: $KUBERAIQ_RG_DEV"
echo "Public web: $KUBERAIQ_PUBLIC_WEB_DEV"
echo "Public API: $KUBERAIQ_PUBLIC_API_DEV"
echo ""

if [[ ! -f "$ENV_FILE" ]]; then
  echo "✗ Missing $ENV_FILE — copy .env.dev.example"
  echo "  cp .env.dev.example .env.dev"
  exit 1
fi
echo "✓ $ENV_FILE exists"

# shellcheck disable=SC1090
set -a && source "$ENV_FILE" && set +a

missing=0
for var in AZURE_RESOURCE_GROUP AZURE_ACR AZURE_POSTGRES_FQDN POSTGRES_ADMIN_PASSWORD; do
  if [[ -z "${!var:-}" ]]; then
    echo "✗ $var is not set (run ./scripts/provision-dev.sh first)"
    missing=1
  else
    echo "✓ $var is set"
  fi
done

echo ""
echo "Mock toggles (dev defaults):"
echo "  USE_MOCK_AUTH=${USE_MOCK_AUTH:-true}"
echo "  USE_MOCK_BILLING=${USE_MOCK_BILLING:-true}"
echo "  USE_MOCK_LLM=${USE_MOCK_LLM:-true}"
echo "  USE_MOCK_WHATSAPP=${USE_MOCK_WHATSAPP:-true}"
echo ""

if [[ "$missing" -eq 0 ]]; then
  echo "Provision (first time): ./scripts/provision-dev.sh"
  echo "Deploy app:           ENV_FILE=$ENV_FILE ./scripts/deploy-dev.sh"
  echo "DNS + domains:        ENV_FILE=$ENV_FILE ./scripts/setup-kuberaiq-dev-domains.sh"
  echo "Verify:               ENV_FILE=$ENV_FILE ./scripts/verify-track-a-dev.sh"
fi

if [[ "$missing" -eq 1 ]]; then
  exit 1
fi
