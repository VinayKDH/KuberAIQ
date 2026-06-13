#!/usr/bin/env bash
# Deploy KuberAIQ to the development resource group (dev.kuberaiq.com).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../infra/azure/naming.sh
source "$ROOT/infra/azure/naming.sh"

export ROOT
export ENV_FILE="${ENV_FILE:-$ROOT/.env.dev}"
export KUBERAIQ_DEPLOY_LABEL="KuberAIQ (development)"
export KUBERAIQ_REQUIRE_STRONG_JWT=false
export KUBERAIQ_VERIFY_SCRIPT=verify-track-a-dev.sh

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Creating $ENV_FILE from .env.dev.example — fill secrets before production-like testing." >&2
  cp "$ROOT/.env.dev.example" "$ENV_FILE"
fi

# Dev defaults (override in .env.dev)
export ENVIRONMENT="${ENVIRONMENT:-dev}"
export AZURE_RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-$KUBERAIQ_RG_DEV}"
export AZURE_API_APP_NAME="${AZURE_API_APP_NAME:-$KUBERAIQ_API_APP_DEV}"
export AZURE_WEB_APP_NAME="${AZURE_WEB_APP_NAME:-$KUBERAIQ_WEB_APP_DEV}"
export AZURE_WEB_HOSTNAME="${AZURE_WEB_HOSTNAME:-${KUBERAIQ_WEB_APP_DEV}.azurewebsites.net}"
export AZURE_API_HOSTNAME="${AZURE_API_HOSTNAME:-${KUBERAIQ_API_APP_DEV}.azurewebsites.net}"
export PUBLIC_WEB_URL="${PUBLIC_WEB_URL:-$KUBERAIQ_PUBLIC_WEB_DEV}"
export PUBLIC_API_URL="${PUBLIC_API_URL:-$KUBERAIQ_PUBLIC_API_DEV}"
export PUBLIC_WEB_DOMAIN="${PUBLIC_WEB_DOMAIN:-dev.kuberaiq.com}"
export PUBLIC_API_DOMAIN="${PUBLIC_API_DOMAIN:-api-dev.kuberaiq.com}"
export USE_MOCK_AUTH="${USE_MOCK_AUTH:-true}"
export USE_MOCK_BILLING="${USE_MOCK_BILLING:-true}"
export USE_MOCK_LLM="${USE_MOCK_LLM:-true}"
export USE_MOCK_WHATSAPP="${USE_MOCK_WHATSAPP:-true}"
export USE_MOCK_BLOB="${USE_MOCK_BLOB:-true}"

# shellcheck source=deploy-kuberaiq-app.sh
source "$ROOT/scripts/deploy-kuberaiq-app.sh"
