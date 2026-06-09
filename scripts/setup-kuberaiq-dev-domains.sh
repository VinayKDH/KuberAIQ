#!/usr/bin/env bash
# Bind dev.kuberaiq.com + api-dev.kuberaiq.com to the development App Services.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../infra/azure/naming.sh
source "$ROOT/infra/azure/naming.sh"

export ENV_FILE="${ENV_FILE:-$ROOT/.env.dev}"
export AZURE_RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-$KUBERAIQ_RG_DEV}"
export AZURE_WEB_APP_NAME="${AZURE_WEB_APP_NAME:-$KUBERAIQ_WEB_APP_DEV}"
export AZURE_API_APP_NAME="${AZURE_API_APP_NAME:-$KUBERAIQ_API_APP_DEV}"
export AZURE_WEB_HOSTNAME="${AZURE_WEB_HOSTNAME:-${KUBERAIQ_WEB_APP_DEV}.azurewebsites.net}"
export AZURE_API_HOSTNAME="${AZURE_API_HOSTNAME:-${KUBERAIQ_API_APP_DEV}.azurewebsites.net}"
export PUBLIC_WEB_DOMAIN="${PUBLIC_WEB_DOMAIN:-dev.kuberaiq.com}"
export PUBLIC_API_DOMAIN="${PUBLIC_API_DOMAIN:-api-dev.kuberaiq.com}"
export PUBLIC_APEX_DOMAIN="${PUBLIC_APEX_DOMAIN:-kuberaiq.com}"
export PUBLIC_WEB_URL="${PUBLIC_WEB_URL:-$KUBERAIQ_PUBLIC_WEB_DEV}"
export PUBLIC_API_URL="${PUBLIC_API_URL:-$KUBERAIQ_PUBLIC_API_DEV}"

exec "$ROOT/scripts/setup-kuberaiq-domains.sh"
