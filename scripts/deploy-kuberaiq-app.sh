#!/usr/bin/env bash
# Shared Azure app deploy (images, settings, migrations) — sourced by deploy-prod.sh / deploy-dev.sh.
set -euo pipefail

: "${ROOT:?ROOT must be set}"
: "${ENV_FILE:?ENV_FILE must be set}"

# shellcheck source=../infra/azure/naming.sh
source "$ROOT/infra/azure/naming.sh"

DEPLOY_LABEL="${KUBERAIQ_DEPLOY_LABEL:-KuberAIQ}"
REQUIRE_STRONG_JWT="${KUBERAIQ_REQUIRE_STRONG_JWT:-true}"
VERIFY_SCRIPT="${KUBERAIQ_VERIFY_SCRIPT:-verify-track-a.sh}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE — copy the matching .env.*.example and fill required values." >&2
  exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

RG="${AZURE_RESOURCE_GROUP:?}"
ACR="${AZURE_ACR:?}"
API_APP="${AZURE_API_APP_NAME:-${KUBERAIQ_API_APP_PROD:-kuberaiq-api-prod}}"
WEB_APP="${AZURE_WEB_APP_NAME:-${KUBERAIQ_WEB_APP_PROD:-kuberaiq-web-prod}}"
WEB_HOST="${AZURE_WEB_HOSTNAME:-${WEB_APP}.azurewebsites.net}"
API_HOST="${AZURE_API_HOSTNAME:-${API_APP}.azurewebsites.net}"

PUBLIC_WEB_URL="${PUBLIC_WEB_URL:-$KUBERAIQ_PUBLIC_WEB_PROD}"
PUBLIC_API_URL="${PUBLIC_API_URL:-$KUBERAIQ_PUBLIC_API_PROD}"
PUBLIC_APEX="${PUBLIC_APEX_DOMAIN:-kuberaiq.com}"

POSTGRES_FQDN="${AZURE_POSTGRES_FQDN:?}"
POSTGRES_LOGIN="${POSTGRES_ADMIN_LOGIN:?}"
POSTGRES_PASSWORD="${POSTGRES_ADMIN_PASSWORD:?}"

JWT_SECRET="${JWT_SECRET:-}"
if [[ "$REQUIRE_STRONG_JWT" == "true" ]]; then
  if [[ -z "$JWT_SECRET" || "$JWT_SECRET" == "dev-only-change-me" ]]; then
    echo "JWT_SECRET is required (generate with: openssl rand -base64 48 | tr -dc 'A-Za-z0-9' | head -c 48)" >&2
    exit 1
  fi
elif [[ -z "$JWT_SECRET" ]]; then
  JWT_SECRET="$(openssl rand -base64 48 | tr -dc 'A-Za-z0-9' | head -c 48)"
  echo "    Generated ephemeral JWT_SECRET for dev deploy"
fi

GOOGLE_CLIENT_ID="${GOOGLE_CLIENT_ID:-}"
GOOGLE_CLIENT_SECRET="${GOOGLE_CLIENT_SECRET:-}"
ENTRA_CLIENT_ID="${ENTRA_CLIENT_ID:-}"
ENTRA_CLIENT_SECRET="${ENTRA_CLIENT_SECRET:-}"
AZURE_OPENAI_ENDPOINT="${AZURE_OPENAI_ENDPOINT:-}"
AZURE_OPENAI_API_KEY="${AZURE_OPENAI_API_KEY:-}"
AZURE_OPENAI_DEPLOYMENT="${AZURE_OPENAI_DEPLOYMENT:-gpt-4o}"
AZURE_OPENAI_API_VERSION="${AZURE_OPENAI_API_VERSION:-2024-08-01-preview}"
AZURE_STORAGE_CONNECTION_STRING="${AZURE_STORAGE_CONNECTION_STRING:-${AZURE_BLOB_CONNECTION_STRING:-}}"
AZURE_STORAGE_CONTAINER="${AZURE_STORAGE_CONTAINER:-${AZURE_BLOB_CONTAINER:-invoices}}"
WHATSAPP_PHONE_NUMBER_ID="${WHATSAPP_PHONE_NUMBER_ID:-}"
WHATSAPP_ACCESS_TOKEN="${WHATSAPP_ACCESS_TOKEN:-}"
WHATSAPP_VERIFY_TOKEN="${WHATSAPP_VERIFY_TOKEN:-$KUBERAIQ_WHATSAPP_VERIFY_TOKEN}"
WHATSAPP_APP_SECRET="${WHATSAPP_APP_SECRET:-}"
RAZORPAY_KEY_ID="${RAZORPAY_KEY_ID:-}"
RAZORPAY_KEY_SECRET="${RAZORPAY_KEY_SECRET:-}"
RAZORPAY_WEBHOOK_SECRET="${RAZORPAY_WEBHOOK_SECRET:-}"
SUBSCRIPTION_PLAN_AMOUNT_PAISE="${SUBSCRIPTION_PLAN_AMOUNT_PAISE:-99900}"

if [[ -z "${USE_MOCK_AUTH+x}" ]]; then
  if [[ -n "$GOOGLE_CLIENT_ID" && -n "$GOOGLE_CLIENT_SECRET" ]] \
    || [[ -n "$ENTRA_CLIENT_ID" && -n "$ENTRA_CLIENT_SECRET" ]]; then
    USE_MOCK_AUTH=false
  else
    USE_MOCK_AUTH=true
  fi
fi
if [[ -z "${USE_MOCK_LLM+x}" ]]; then
  if [[ -n "$AZURE_OPENAI_ENDPOINT" && -n "$AZURE_OPENAI_API_KEY" ]]; then
    USE_MOCK_LLM=false
  else
    USE_MOCK_LLM=true
  fi
fi
if [[ -z "${USE_MOCK_BLOB+x}" ]]; then
  if [[ -n "$AZURE_STORAGE_CONNECTION_STRING" ]]; then
    USE_MOCK_BLOB=false
  else
    USE_MOCK_BLOB=true
  fi
fi
if [[ -z "${USE_MOCK_WHATSAPP+x}" ]]; then
  if [[ -n "$WHATSAPP_PHONE_NUMBER_ID" && -n "$WHATSAPP_ACCESS_TOKEN" ]]; then
    USE_MOCK_WHATSAPP=false
  else
    USE_MOCK_WHATSAPP=true
  fi
fi
if [[ -z "${USE_MOCK_BILLING+x}" ]]; then
  if [[ -n "$RAZORPAY_KEY_ID" && -n "$RAZORPAY_KEY_SECRET" && -n "$RAZORPAY_WEBHOOK_SECRET" ]]; then
    USE_MOCK_BILLING=false
  else
    USE_MOCK_BILLING=true
  fi
fi

BUILD_API_URL="$PUBLIC_API_URL"
BUILD_WEB_URL="$PUBLIC_WEB_URL"
if ! curl -sf --max-time 5 "${PUBLIC_API_URL}/health" >/dev/null 2>&1; then
  BUILD_API_URL="https://${API_HOST}"
  echo "    Note: ${PUBLIC_API_URL} unreachable — building web with API ${BUILD_API_URL}"
fi
if ! curl -sf --max-time 5 "${PUBLIC_WEB_URL}" >/dev/null 2>&1; then
  BUILD_WEB_URL="https://${WEB_HOST}"
  echo "    Note: ${PUBLIC_WEB_URL} unreachable — building web with ${BUILD_WEB_URL}"
fi

CORS_JSON="${CORS_ORIGINS:-}"

echo "==> Deploying $DEPLOY_LABEL"
echo "    Web (public):  $PUBLIC_WEB_URL"
echo "    API (public):  $PUBLIC_API_URL"
echo "    Web (build):   $BUILD_WEB_URL"
echo "    API (build):   $BUILD_API_URL"
echo "    Mock auth:     $USE_MOCK_AUTH"
echo "    Mock LLM:      $USE_MOCK_LLM"
echo "    Mock blob:     $USE_MOCK_BLOB"
echo "    Mock WhatsApp: $USE_MOCK_WHATSAPP"
echo "    Mock billing:  $USE_MOCK_BILLING"

echo "==> Building API image"
az acr build --registry "$ACR" --image "${KUBERAIQ_IMAGE_API}:latest" "$ROOT/backend" --output none

echo "==> Building Web image"
BUILD_ARGS=(
  --build-arg "NEXT_PUBLIC_API_URL=$BUILD_API_URL"
  --build-arg "API_UPSTREAM_URL=$BUILD_API_URL"
  --build-arg "NEXT_PUBLIC_WEB_URL=$BUILD_WEB_URL"
  --build-arg "NEXT_PUBLIC_USE_MOCK_AUTH=$USE_MOCK_AUTH"
  --build-arg "NEXT_PUBLIC_GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID"
  --build-arg "NEXT_PUBLIC_GOOGLE_REDIRECT_URI=${GOOGLE_REDIRECT_URI:-$PUBLIC_WEB_URL/auth/callback}"
  --build-arg "NEXT_PUBLIC_OAUTH_COOKIE_DOMAIN=.${PUBLIC_APEX:-kuberaiq.com}"
  --build-arg "NEXT_PUBLIC_APEX_DOMAIN=${PUBLIC_APEX:-kuberaiq.com}"
  --build-arg "NEXT_PUBLIC_USE_MOCK_BILLING=$USE_MOCK_BILLING"
)
if [[ -n "${ENTRA_CLIENT_ID:-}" ]]; then
  BUILD_ARGS+=(
    --build-arg "NEXT_PUBLIC_ENTRA_CLIENT_ID=$ENTRA_CLIENT_ID"
    --build-arg "NEXT_PUBLIC_ENTRA_TENANT_ID=${ENTRA_TENANT_ID:-common}"
    --build-arg "NEXT_PUBLIC_ENTRA_REDIRECT_URI=${ENTRA_REDIRECT_URI:-$PUBLIC_WEB_URL/auth/callback}"
  )
fi
az acr build --registry "$ACR" --image "${KUBERAIQ_IMAGE_WEB}:latest" "${BUILD_ARGS[@]}" "$ROOT/frontend" --output none

ACR_LOGIN=$(az acr show --name "$ACR" --resource-group "$RG" --query loginServer -o tsv)

echo "==> Updating API settings"
API_SETTINGS_FILE="$(mktemp)"
DEPLOY_ENVIRONMENT="${ENVIRONMENT:-dev}" \
  JWT_SECRET="$JWT_SECRET" \
  USE_MOCK_AUTH="$USE_MOCK_AUTH" \
  USE_MOCK_LLM="$USE_MOCK_LLM" \
  USE_MOCK_BLOB="$USE_MOCK_BLOB" \
  USE_MOCK_WHATSAPP="$USE_MOCK_WHATSAPP" \
  USE_MOCK_BILLING="$USE_MOCK_BILLING" \
  CORS_JSON="$CORS_JSON" \
  PUBLIC_WEB_URL="$PUBLIC_WEB_URL" \
  PUBLIC_API_URL="$PUBLIC_API_URL" \
  PUBLIC_APEX="$PUBLIC_APEX" \
  WEB_HOST="$WEB_HOST" \
  GOOGLE_CLIENT_ID="$GOOGLE_CLIENT_ID" \
  GOOGLE_CLIENT_SECRET="$GOOGLE_CLIENT_SECRET" \
  ENTRA_TENANT_ID="${ENTRA_TENANT_ID:-}" \
  ENTRA_CLIENT_ID="${ENTRA_CLIENT_ID:-}" \
  ENTRA_CLIENT_SECRET="${ENTRA_CLIENT_SECRET:-}" \
  AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
  AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
  AZURE_OPENAI_DEPLOYMENT="$AZURE_OPENAI_DEPLOYMENT" \
  AZURE_OPENAI_API_VERSION="$AZURE_OPENAI_API_VERSION" \
  AZURE_STORAGE_CONNECTION_STRING="$AZURE_STORAGE_CONNECTION_STRING" \
  AZURE_STORAGE_CONTAINER="$AZURE_STORAGE_CONTAINER" \
  WHATSAPP_PHONE_NUMBER_ID="$WHATSAPP_PHONE_NUMBER_ID" \
  WHATSAPP_ACCESS_TOKEN="$WHATSAPP_ACCESS_TOKEN" \
  WHATSAPP_VERIFY_TOKEN="$WHATSAPP_VERIFY_TOKEN" \
  WHATSAPP_APP_SECRET="$WHATSAPP_APP_SECRET" \
  RAZORPAY_KEY_ID="$RAZORPAY_KEY_ID" \
  RAZORPAY_KEY_SECRET="$RAZORPAY_KEY_SECRET" \
  RAZORPAY_WEBHOOK_SECRET="$RAZORPAY_WEBHOOK_SECRET" \
  SUBSCRIPTION_PLAN_AMOUNT_PAISE="$SUBSCRIPTION_PLAN_AMOUNT_PAISE" \
  POSTGRES_LOGIN="$POSTGRES_LOGIN" \
  POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  POSTGRES_FQDN="$POSTGRES_FQDN" \
  KUBERAIQ_DB_NAME="$KUBERAIQ_DB_NAME" \
  python3 - "$API_SETTINGS_FILE" <<'PY'
import json, os, sys
path = sys.argv[1]
cors_raw = os.environ.get("CORS_JSON", "").strip()
if cors_raw:
    try:
        cors_origins = json.loads(cors_raw)
    except json.JSONDecodeError:
        cors_origins = [
            p.strip() for p in cors_raw.strip("[]").split(",") if p.strip()
        ]
else:
    cors_origins = [
        os.environ.get("PUBLIC_WEB_URL", "https://www.kuberaiq.com"),
        f"https://{os.environ.get('PUBLIC_APEX', 'kuberaiq.com')}",
        os.environ.get("PUBLIC_API_URL", "https://api.kuberaiq.com"),
        f"https://{os.environ.get('WEB_HOST', 'kuberaiq-web-prod.azurewebsites.net')}",
    ]
pg_login = os.environ.get("POSTGRES_LOGIN", "")
pg_password = os.environ.get("POSTGRES_PASSWORD", "")
pg_fqdn = os.environ.get("POSTGRES_FQDN", "")
pg_db = os.environ.get("KUBERAIQ_DB_NAME", "kuberaiq")
settings = {
    "ENVIRONMENT": os.environ.get("DEPLOY_ENVIRONMENT", "dev"),
    "DATABASE_URL": (
        f"postgresql+asyncpg://{pg_login}:{pg_password}@{pg_fqdn}:5432/{pg_db}?ssl=require"
        if pg_login and pg_password and pg_fqdn
        else ""
    ),
    "JWT_SECRET": os.environ["JWT_SECRET"],
    "USE_MOCK_AUTH": os.environ["USE_MOCK_AUTH"],
    "USE_MOCK_LLM": os.environ["USE_MOCK_LLM"],
    "USE_MOCK_BLOB": os.environ["USE_MOCK_BLOB"],
    "USE_MOCK_WHATSAPP": os.environ["USE_MOCK_WHATSAPP"],
    "USE_MOCK_BILLING": os.environ["USE_MOCK_BILLING"],
    "CORS_ORIGINS": json.dumps(cors_origins),
    "GOOGLE_CLIENT_ID": os.environ.get("GOOGLE_CLIENT_ID", ""),
    "GOOGLE_CLIENT_SECRET": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
    "ENTRA_TENANT_ID": os.environ.get("ENTRA_TENANT_ID", ""),
    "ENTRA_CLIENT_ID": os.environ.get("ENTRA_CLIENT_ID", ""),
    "ENTRA_CLIENT_SECRET": os.environ.get("ENTRA_CLIENT_SECRET", ""),
    "AZURE_OPENAI_ENDPOINT": os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
    "AZURE_OPENAI_API_KEY": os.environ.get("AZURE_OPENAI_API_KEY", ""),
    "AZURE_OPENAI_DEPLOYMENT": os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
    "AZURE_OPENAI_API_VERSION": os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
    "AZURE_STORAGE_CONTAINER": os.environ.get("AZURE_STORAGE_CONTAINER", "invoices"),
    "WHATSAPP_PHONE_NUMBER_ID": os.environ.get("WHATSAPP_PHONE_NUMBER_ID", ""),
    "WHATSAPP_ACCESS_TOKEN": os.environ.get("WHATSAPP_ACCESS_TOKEN", ""),
    "WHATSAPP_VERIFY_TOKEN": os.environ.get("WHATSAPP_VERIFY_TOKEN", "kuberaiq-verify"),
    "WHATSAPP_APP_SECRET": os.environ.get("WHATSAPP_APP_SECRET", ""),
    "RAZORPAY_KEY_ID": os.environ.get("RAZORPAY_KEY_ID", ""),
    "RAZORPAY_KEY_SECRET": os.environ.get("RAZORPAY_KEY_SECRET", ""),
    "RAZORPAY_WEBHOOK_SECRET": os.environ.get("RAZORPAY_WEBHOOK_SECRET", ""),
    "SUBSCRIPTION_PLAN_AMOUNT_PAISE": os.environ.get("SUBSCRIPTION_PLAN_AMOUNT_PAISE", "99900"),
}
cs = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
if cs:
    settings["AZURE_STORAGE_CONNECTION_STRING"] = cs
settings = {k: v for k, v in settings.items() if v != ""}
with open(path, "w", encoding="utf-8") as f:
    json.dump(settings, f)
PY
az webapp config appsettings set --resource-group "$RG" --name "$API_APP" --settings "@${API_SETTINGS_FILE}" --output none
rm -f "$API_SETTINGS_FILE"

echo "==> Refreshing containers"
az webapp config set --resource-group "$RG" --name "$API_APP" \
  --linux-fx-version "DOCKER|${ACR_LOGIN}/${KUBERAIQ_IMAGE_API}:latest" --output none
az webapp config set --resource-group "$RG" --name "$WEB_APP" \
  --linux-fx-version "DOCKER|${ACR_LOGIN}/${KUBERAIQ_IMAGE_WEB}:latest" --output none
az webapp stop --resource-group "$RG" --name "$API_APP" --output none
az webapp stop --resource-group "$RG" --name "$WEB_APP" --output none
sleep 5
az webapp start --resource-group "$RG" --name "$API_APP" --output none
az webapp start --resource-group "$RG" --name "$WEB_APP" --output none

echo "==> Running migrations"
export DATABASE_URL="postgresql+asyncpg://${POSTGRES_LOGIN}:${POSTGRES_PASSWORD}@${POSTGRES_FQDN}:5432/${KUBERAIQ_DB_NAME}?ssl=require"
cd "$ROOT/backend"
# Sourcing .env.* strips JSON quotes from CORS_ORIGINS; pydantic rejects the mangled value.
unset CORS_ORIGINS
if ! alembic upgrade head; then
  echo "WARNING: Migration failed (Postgres timeout or busy). Apps are deployed — retry:"
  echo "  cd backend && DATABASE_URL=... alembic upgrade head"
else
  CURRENT_REV=$(alembic current 2>/dev/null | awk '{print $1}' | head -1 || true)
  echo "    Alembic at: ${CURRENT_REV:-unknown}"
fi

SMOKE_API_URL="$BUILD_API_URL"
if curl -sf --max-time 10 "${PUBLIC_API_URL}/health" >/dev/null 2>&1; then
  SMOKE_API_URL="$PUBLIC_API_URL"
fi

echo "==> Smoke tests ($SMOKE_API_URL)"
curl -sf "${SMOKE_API_URL}/health" | grep -q '"status":"ok"'
curl -sf "${SMOKE_API_URL}/health/ready" | grep -q '"database":"ok"' || echo "WARNING: DB ready check failed (may be cold start)"

INTEGRATIONS=$(curl -sf "${SMOKE_API_URL}/health/integrations" || echo '{}')
echo "    Integrations: $INTEGRATIONS"

if [[ "$USE_MOCK_AUTH" == "false" ]]; then
  MOCK_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${SMOKE_API_URL}/api/v1/auth/mock-login" \
    -H "Content-Type: application/json" -d '{"email":"owner@demo.kuberaiq.com"}')
  if [[ "$MOCK_STATUS" != "403" ]]; then
    echo "WARNING: Expected mock-login 403 when USE_MOCK_AUTH=false, got $MOCK_STATUS"
  else
    echo "    Auth: mock-login correctly disabled (403)"
  fi
fi

if [[ -n "$WHATSAPP_VERIFY_TOKEN" ]]; then
  WA_CHALLENGE="kuberaiq-deploy-$(date +%s)"
  WA_BODY=$(curl -sf "${SMOKE_API_URL}/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=${WHATSAPP_VERIFY_TOKEN}&hub.challenge=${WA_CHALLENGE}" || true)
  if [[ "$WA_BODY" == "$WA_CHALLENGE" ]]; then
    echo "    WhatsApp webhook verify: OK"
  else
    echo "WARNING: WhatsApp webhook verify failed (check WHATSAPP_VERIFY_TOKEN)"
  fi
fi

curl -sf -o /dev/null -w "    Web Azure HTTP %{http_code}\n" "https://${WEB_HOST}"

echo ""
echo "Deploy complete."
echo "  Azure web:  https://${WEB_HOST}"
echo "  Azure API:  https://${API_HOST}"
echo "  Public web: ${PUBLIC_WEB_URL}"
echo "  Public API: ${PUBLIC_API_URL}"
echo ""
echo "Next: ENV_FILE=$ENV_FILE ./scripts/${VERIFY_SCRIPT}"
