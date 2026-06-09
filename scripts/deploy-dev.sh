#!/usr/bin/env bash
# Deploy KuberAIQ to the development resource group (dev.kuberaiq.com).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../infra/azure/naming.sh
source "$ROOT/infra/azure/naming.sh"

export ENVIRONMENT=dev
export RESOURCE_GROUP="${RESOURCE_GROUP:-$KUBERAIQ_RG_DEV}"
export ENV_FILE="${ENV_FILE:-$ROOT/.env.dev}"

echo "==> KuberAIQ development deploy → $RESOURCE_GROUP"
echo "    Public web: $KUBERAIQ_PUBLIC_WEB_DEV"
echo "    Public API: $KUBERAIQ_PUBLIC_API_DEV"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Creating $ENV_FILE from .env.dev.example — fill secrets before app deploy." >&2
  cp "$ROOT/.env.dev.example" "$ENV_FILE"
fi

exec "$ROOT/scripts/deploy-azure.sh"
