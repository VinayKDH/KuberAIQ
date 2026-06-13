#!/usr/bin/env bash
# Verify Track A development integrations (dev.kuberaiq.com).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../infra/azure/naming.sh
source "$ROOT/infra/azure/naming.sh"

export ENV_FILE="${ENV_FILE:-$ROOT/.env.dev}"
export PUBLIC_WEB_DOMAIN="${PUBLIC_WEB_DOMAIN:-dev.kuberaiq.com}"
export PUBLIC_API_DOMAIN="${PUBLIC_API_DOMAIN:-api-dev.kuberaiq.com}"
export PUBLIC_WEB_URL="${PUBLIC_WEB_URL:-$KUBERAIQ_PUBLIC_WEB_DEV}"
export PUBLIC_API_URL="${PUBLIC_API_URL:-$KUBERAIQ_PUBLIC_API_DEV}"
export AZURE_WEB_HOSTNAME="${AZURE_WEB_HOSTNAME:-${KUBERAIQ_WEB_APP_DEV}.azurewebsites.net}"
export AZURE_API_HOSTNAME="${AZURE_API_HOSTNAME:-${KUBERAIQ_API_APP_DEV}.azurewebsites.net}"
export USE_MOCK_AUTH="${USE_MOCK_AUTH:-true}"
export USE_MOCK_BILLING="${USE_MOCK_BILLING:-true}"

exec "$ROOT/scripts/verify-track-a.sh"
