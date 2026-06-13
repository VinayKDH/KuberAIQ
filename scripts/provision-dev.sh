#!/usr/bin/env bash
# Provision KuberAIQ development infrastructure (rg-kuberaiq-dev) via Bicep.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../infra/azure/naming.sh
source "$ROOT/infra/azure/naming.sh"

export ENVIRONMENT=dev
export RESOURCE_GROUP="${RESOURCE_GROUP:-$KUBERAIQ_RG_DEV}"
export POSTGRES_ADMIN_LOGIN="${POSTGRES_ADMIN_LOGIN:-$KUBERAIQ_DB_ADMIN_LOGIN}"

echo "==> Provisioning KuberAIQ development infrastructure"
echo "    Resource group: $RESOURCE_GROUP"
echo "    Custom domains: $KUBERAIQ_PUBLIC_WEB_DEV / $KUBERAIQ_PUBLIC_API_DEV"

"$ROOT/scripts/deploy-azure.sh"

OUT_FILE="$ROOT/.env.dev.generated"
python3 - <<'PY' > "$OUT_FILE"
import json, os, subprocess

rg = os.environ["RESOURCE_GROUP"]
result = subprocess.run(
    [
        "az", "deployment", "group", "list", "-g", rg,
        "--query", "sort_by([?starts_with(name, 'kuberaiq-dev-')], &properties.timestamp)[-1].properties.outputs",
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
    f"AZURE_WEB_HOSTNAME={out('webAppName', 'kuberaiq-web-dev')}.azurewebsites.net",
    f"AZURE_API_HOSTNAME={out('apiAppName', 'kuberaiq-api-dev')}.azurewebsites.net",
    f"AZURE_POSTGRES_FQDN={out('postgresServerFqdn')}",
    f"POSTGRES_ADMIN_LOGIN={os.environ.get('POSTGRES_ADMIN_LOGIN', 'kuberaiqadmin')}",
    "# POSTGRES_ADMIN_PASSWORD=<from deploy-azure.sh output>",
    f"PUBLIC_WEB_URL={os.environ.get('KUBERAIQ_PUBLIC_WEB_DEV', 'https://dev.kuberaiq.com')}",
    f"PUBLIC_API_URL={os.environ.get('KUBERAIQ_PUBLIC_API_DEV', 'https://api-dev.kuberaiq.com')}",
    f"PUBLIC_WEB_DOMAIN=dev.kuberaiq.com",
    f"PUBLIC_API_DOMAIN=api-dev.kuberaiq.com",
]
print("\n".join(lines))
PY

echo ""
echo "Wrote $OUT_FILE — merge into .env.dev, then:"
echo "  ENV_FILE=.env.dev ./scripts/deploy-dev.sh"
echo "  ENV_FILE=.env.dev ./scripts/setup-kuberaiq-dev-domains.sh"
