#!/usr/bin/env bash
# Deploy KuberAIQ to Azure with www.kuberaiq.com + api.kuberaiq.com configuration.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export ROOT
export ENV_FILE="${ENV_FILE:-$ROOT/.env.prod}"
export KUBERAIQ_DEPLOY_LABEL="KuberAIQ (Track A production)"
export KUBERAIQ_REQUIRE_STRONG_JWT=true
export KUBERAIQ_VERIFY_SCRIPT=verify-track-a.sh

# shellcheck source=deploy-kuberaiq-app.sh
source "$ROOT/scripts/deploy-kuberaiq-app.sh"
