#!/usr/bin/env bash
# Provision KuberAIQ production infrastructure (rg-kuberaiq-prod) via Bicep.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../infra/azure/naming.sh
source "$ROOT/infra/azure/naming.sh"

export ENVIRONMENT=prod
export RESOURCE_GROUP="${RESOURCE_GROUP:-$KUBERAIQ_RG_PROD}"
export POSTGRES_ADMIN_LOGIN="${POSTGRES_ADMIN_LOGIN:-$KUBERAIQ_DB_ADMIN_LOGIN}"

echo "==> Provisioning KuberAIQ production infrastructure"
echo "    Resource group: $RESOURCE_GROUP"
echo "    Custom domains:   $KUBERAIQ_PUBLIC_WEB_PROD / $KUBERAIQ_PUBLIC_API_PROD"

"$ROOT/scripts/deploy-azure.sh"

OUT_FILE="$ROOT/.env.prod.generated"
python3 - <<'PY' > "$OUT_FILE"
import json, os, subprocess, sys

rg = os.environ["RESOURCE_GROUP"]
result = subprocess.run(
    [
        "az", "deployment", "group", "list", "-g", rg,
        "--query", "sort_by([?starts_with(name, 'kuberaiq-prod-')], &properties.timestamp)[-1].properties.outputs",
        "-o", "json",
    ],
    capture_output=True, text=True, check=True,
)
outputs = {k: v["value"] for k, v in json.loads(result.stdout or "{}").items()}

def out(key, default=""):
    return outputs.get(key, default)

lines = [
    f"AZURE_RESOURCE_GROUP={rg}",
    f"AZURE_ACR={out('acrName')}",
    f"AZURE_API_APP_NAME={out('apiAppName')}",
    f"AZURE_WEB_APP_NAME={out('webAppName')}",
    f"AZURE_WEB_HOSTNAME={out('webAppName', 'kuberaiq-web-prod')}.azurewebsites.net",
    f"AZURE_API_HOSTNAME={out('apiAppName', 'kuberaiq-api-prod')}.azurewebsites.net",
    f"AZURE_POSTGRES_FQDN={out('postgresServerFqdn')}",
    f"POSTGRES_ADMIN_LOGIN={os.environ.get('POSTGRES_ADMIN_LOGIN', 'kuberaiqadmin')}",
    "# POSTGRES_ADMIN_PASSWORD=<from deploy-azure.sh output>",
    f"PUBLIC_WEB_URL={os.environ.get('KUBERAIQ_PUBLIC_WEB_PROD', 'https://www.kuberaiq.com')}",
    f"PUBLIC_API_URL={os.environ.get('KUBERAIQ_PUBLIC_API_PROD', 'https://api.kuberaiq.com')}",
]
print("\n".join(lines))
PY

echo ""
echo "Wrote $OUT_FILE — merge into .env.prod (keep JWT_SECRET, OAuth secrets), then:"
echo "  ENV_FILE=.env.prod ./scripts/deploy-prod.sh"
echo "  ENV_FILE=.env.prod ./scripts/setup-kuberaiq-domains.sh"
