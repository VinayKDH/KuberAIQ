#!/usr/bin/env bash
# Deploy KuberAIQ infrastructure and container images to Azure.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../infra/azure/naming.sh
source "$ROOT/infra/azure/naming.sh"

ENVIRONMENT="${ENVIRONMENT:-dev}"
LOCATION="${LOCATION:-southindia}"
POSTGRES_LOCATION="${POSTGRES_LOCATION:-centralindia}"
if [[ -z "${RESOURCE_GROUP:-}" ]]; then
  if [[ "$ENVIRONMENT" == "prod" ]]; then
    RESOURCE_GROUP="$KUBERAIQ_RG_PROD"
  else
    RESOURCE_GROUP="$KUBERAIQ_RG_DEV"
  fi
fi
DEPLOYMENT_NAME="kuberaiq-${ENVIRONMENT}-$(date +%Y%m%d%H%M%S)"
SKIP_IMAGES="${SKIP_IMAGES:-false}"

POSTGRES_ADMIN_LOGIN="${POSTGRES_ADMIN_LOGIN:-$KUBERAIQ_DB_ADMIN_LOGIN}"
POSTGRES_ADMIN_PASSWORD="${POSTGRES_ADMIN_PASSWORD:-$(openssl rand -base64 24 | tr -dc 'A-Za-z0-9' | head -c 24)}"
JWT_SECRET="${JWT_SECRET:-$(openssl rand -base64 48 | tr -dc 'A-Za-z0-9' | head -c 48)}"
OPENAI_API_KEY="${OPENAI_API_KEY:-placeholder-replace-me}"

echo "==> Deploying KuberAIQ to Azure"
echo "    Environment:  $ENVIRONMENT"
echo "    Location:     $LOCATION"
echo "    Postgres:     $POSTGRES_LOCATION"
echo "    Resource grp: $RESOURCE_GROUP"

if ! command -v az >/dev/null 2>&1; then
  echo "Azure CLI (az) is required." >&2
  exit 1
fi

echo "==> Ensuring resource group exists"
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none

echo "==> Registering required resource providers"
for provider in Microsoft.Web Microsoft.DBforPostgreSQL Microsoft.KeyVault Microsoft.Storage Microsoft.ContainerRegistry Microsoft.OperationalInsights Microsoft.Insights; do
  az provider register --namespace "$provider" --wait --output none 2>/dev/null || true
done

echo "==> Deploying Bicep template (this may take 10-15 minutes)"
DEPLOY_OUTPUT="$(
  az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DEPLOYMENT_NAME" \
    --template-file "$ROOT/infra/bicep/main.bicep" \
    --parameters \
      environmentName="$ENVIRONMENT" \
      location="$LOCATION" \
      postgresLocation="$POSTGRES_LOCATION" \
      postgresAdminLogin="$POSTGRES_ADMIN_LOGIN" \
      postgresAdminPassword="$POSTGRES_ADMIN_PASSWORD" \
      jwtSecret="$JWT_SECRET" \
      openaiApiKey="$OPENAI_API_KEY" \
    --query properties.outputs \
    --output json
)"

API_APP_NAME="$(echo "$DEPLOY_OUTPUT" | python3 -c "import json,sys; print(json.load(sys.stdin)['apiAppName']['value'])")"
WEB_APP_NAME="$(echo "$DEPLOY_OUTPUT" | python3 -c "import json,sys; print(json.load(sys.stdin)['webAppName']['value'])")"
ACR_NAME="$(echo "$DEPLOY_OUTPUT" | python3 -c "import json,sys; print(json.load(sys.stdin)['acrName']['value'])")"
API_URL="$(echo "$DEPLOY_OUTPUT" | python3 -c "import json,sys; print(json.load(sys.stdin)['apiAppUrl']['value'])")"
WEB_URL="$(echo "$DEPLOY_OUTPUT" | python3 -c "import json,sys; print(json.load(sys.stdin)['webAppUrl']['value'])")"
PG_FQDN="$(echo "$DEPLOY_OUTPUT" | python3 -c "import json,sys; print(json.load(sys.stdin)['postgresServerFqdn']['value'])")"
KV_NAME="$(echo "$DEPLOY_OUTPUT" | python3 -c "import json,sys; print(json.load(sys.stdin)['keyVaultName']['value'])")"

if [[ "$SKIP_IMAGES" != "true" ]]; then
  echo "==> Waiting for ACR to become available"
  for _ in 1 2 3 4 5 6; do
    if az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --output none 2>/dev/null; then
      break
    fi
    sleep 10
  done

  echo "==> Building API image in ACR (cloud build — no local Docker required)"
  az acr build \
    --registry "$ACR_NAME" \
    --image "${KUBERAIQ_IMAGE_API}:latest" \
    "$ROOT/backend"

  echo "==> Building Web image in ACR"
  az acr build \
    --registry "$ACR_NAME" \
    --image "${KUBERAIQ_IMAGE_WEB}:latest" \
    --build-arg "NEXT_PUBLIC_API_URL=$API_URL" \
    "$ROOT/frontend"

  echo "==> Restarting App Services to pull latest images"
  az webapp restart --resource-group "$RESOURCE_GROUP" --name "$API_APP_NAME"
  az webapp restart --resource-group "$RESOURCE_GROUP" --name "$WEB_APP_NAME"
else
  echo "==> Skipping image build (SKIP_IMAGES=true)"
fi

echo ""
echo "Deployment complete."
echo "  API:        $API_URL"
echo "  Web:        $WEB_URL"
echo "  PostgreSQL: $PG_FQDN"
echo "  Key Vault:  $KV_NAME"
echo "  ACR:        $ACR_NAME"
echo ""
echo "Save these credentials securely (not committed to git):"
echo "  POSTGRES_ADMIN_LOGIN=$POSTGRES_ADMIN_LOGIN"
echo "  POSTGRES_ADMIN_PASSWORD=$POSTGRES_ADMIN_PASSWORD"
echo ""
echo "Next steps:"
echo "  1. Update Key Vault secret 'openai-api-key' with your Azure OpenAI key"
echo "  2. Run DB migrations against the PostgreSQL server"
echo "  3. Open $WEB_URL and sign in (mock auth enabled until Entra is configured)"
