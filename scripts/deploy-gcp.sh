#!/usr/bin/env bash
# Deploy KuberAIQ API + Web to GCP Cloud Run while keeping Azure live.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -z "${ENV_FILE:-}" ]]; then
  if [[ -f "$ROOT/.env.gcp" ]]; then
    ENV_FILE="$ROOT/.env.gcp"
  else
    ENV_FILE="$ROOT/.env.prod"
  fi
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing ENV_FILE: $ENV_FILE (copy .env.gcp.example to .env.gcp)" >&2
  exit 1
fi

# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_REGION:-asia-south1}"
AR_REPO="${GCP_ARTIFACT_REPO:-kuberaiq}"
API_SERVICE="${GCP_API_SERVICE:-kuberaiq-api-gcp}"
WEB_SERVICE="${GCP_WEB_SERVICE:-kuberaiq-web-gcp}"
DB_NAME="${KUBERAIQ_DB_NAME:-kuberaiq}"
IMAGE_TAG="${GCP_IMAGE_TAG:-$(date +%Y%m%d%H%M%S)}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "Set GCP_PROJECT_ID or configure gcloud default project." >&2
  exit 1
fi

GCP_CLOUDSQL_INSTANCE="${GCP_CLOUDSQL_INSTANCE:-}"
GCP_CLOUDSQL_CONNECTION_NAME="${GCP_CLOUDSQL_CONNECTION_NAME:-}"
GCP_DB_USER="${GCP_DB_USER:-kuberaiq}"
GCP_DB_PASSWORD="${GCP_DB_PASSWORD:-}"
DATABASE_URL="${DATABASE_URL:-}"

if [[ -z "$DATABASE_URL" && -n "$GCP_CLOUDSQL_CONNECTION_NAME" && -n "$GCP_DB_PASSWORD" ]]; then
  DATABASE_URL="postgresql+asyncpg://${GCP_DB_USER}:${GCP_DB_PASSWORD}@localhost/${DB_NAME}?host=/cloudsql/${GCP_CLOUDSQL_CONNECTION_NAME}"
elif [[ -z "$DATABASE_URL" && -n "$GCP_CLOUDSQL_INSTANCE" && -n "$GCP_DB_PASSWORD" ]]; then
  GCP_CLOUDSQL_CONNECTION_NAME="${PROJECT_ID}:${REGION}:${GCP_CLOUDSQL_INSTANCE}"
  DATABASE_URL="postgresql+asyncpg://${GCP_DB_USER}:${GCP_DB_PASSWORD}@localhost/${DB_NAME}?host=/cloudsql/${GCP_CLOUDSQL_CONNECTION_NAME}"
fi

POSTGRES_FQDN="${AZURE_POSTGRES_FQDN:-}"
POSTGRES_LOGIN="${POSTGRES_ADMIN_LOGIN:-}"
POSTGRES_PASSWORD="${POSTGRES_ADMIN_PASSWORD:-}"
if [[ -z "$DATABASE_URL" && -n "$POSTGRES_FQDN" && -n "$POSTGRES_LOGIN" && -n "$POSTGRES_PASSWORD" ]]; then
  DATABASE_URL="postgresql+asyncpg://${POSTGRES_LOGIN}:${POSTGRES_PASSWORD}@${POSTGRES_FQDN}:5432/${DB_NAME}?ssl=require"
fi

export DATABASE_URL
if [[ -z "$DATABASE_URL" ]]; then
  echo "DATABASE_URL is required (set GCP Cloud SQL vars or AZURE_POSTGRES_* in ENV_FILE)." >&2
  exit 1
fi

CLOUDSQL_ANNOTATION=()
if [[ -n "$GCP_CLOUDSQL_CONNECTION_NAME" ]]; then
  CLOUDSQL_ANNOTATION=(--add-cloudsql-instances="$GCP_CLOUDSQL_CONNECTION_NAME")
fi

ENVIRONMENT="${ENVIRONMENT:-production}"

# Production mock toggles — set explicitly in .env.gcp or infer from configured credentials.
if [[ -z "${USE_MOCK_AUTH+x}" ]]; then
  if [[ -n "${GOOGLE_CLIENT_ID:-}" && -n "${GOOGLE_CLIENT_SECRET:-}" ]] \
    || [[ -n "${ENTRA_CLIENT_ID:-}" && -n "${ENTRA_CLIENT_SECRET:-}" ]]; then
    USE_MOCK_AUTH=false
  else
    USE_MOCK_AUTH=false
  fi
fi
if [[ -z "${USE_MOCK_BILLING+x}" ]]; then
  if [[ -n "${RAZORPAY_KEY_ID:-}" && -n "${RAZORPAY_KEY_SECRET:-}" && -n "${RAZORPAY_WEBHOOK_SECRET:-}" ]]; then
    USE_MOCK_BILLING=false
  else
    USE_MOCK_BILLING=false
  fi
fi
if [[ -z "${USE_MOCK_WHATSAPP+x}" ]]; then
  if [[ -n "${WHATSAPP_PHONE_NUMBER_ID:-}" && -n "${WHATSAPP_ACCESS_TOKEN:-}" ]]; then
    USE_MOCK_WHATSAPP=false
  else
    USE_MOCK_WHATSAPP=true
  fi
fi
if [[ -z "${USE_MOCK_BLOB+x}" ]]; then
  if [[ -n "${AZURE_STORAGE_CONNECTION_STRING:-}" ]]; then
    USE_MOCK_BLOB=false
  else
    USE_MOCK_BLOB=true
  fi
fi
if [[ -z "${USE_MOCK_LLM+x}" ]]; then
  if [[ -n "${AZURE_OPENAI_ENDPOINT:-}" && -n "${AZURE_OPENAI_API_KEY:-}" ]]; then
    USE_MOCK_LLM=false
  else
    USE_MOCK_LLM=true
  fi
fi
export USE_MOCK_AUTH USE_MOCK_BLOB USE_MOCK_BILLING USE_MOCK_WHATSAPP USE_MOCK_LLM ENVIRONMENT

echo "==> Production mode"
echo "    Environment:   $ENVIRONMENT"
echo "    Mock auth:     $USE_MOCK_AUTH"
echo "    Mock billing:  $USE_MOCK_BILLING"
echo "    Mock WhatsApp: $USE_MOCK_WHATSAPP"
echo "    Mock blob:     $USE_MOCK_BLOB"
echo "    Mock LLM:      $USE_MOCK_LLM"

WEB_URL_FOR_BUILD="$(gcloud run services describe "$WEB_SERVICE" --region "$REGION" --project "$PROJECT_ID" --format='value(status.url)' 2>/dev/null || true)"
export GCP_WEB_ORIGIN="${GCP_WEB_ORIGIN:-$WEB_URL_FOR_BUILD}"

if ! gcloud services list --enabled --project "$PROJECT_ID" --format="value(config.name)" | rg -q "^run.googleapis.com$"; then
  gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project "$PROJECT_ID"
fi

if ! gcloud artifacts repositories describe "$AR_REPO" --location "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$AR_REPO" \
    --repository-format=docker \
    --location="$REGION" \
    --description="KuberAIQ images" \
    --project "$PROJECT_ID"
fi

IMAGE_BASE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}"
API_IMAGE="${IMAGE_BASE}/kuberaiq-api:${IMAGE_TAG}"
WEB_IMAGE="${IMAGE_BASE}/kuberaiq-web:${IMAGE_TAG}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "==> Building and pushing API image"
gcloud builds submit "$ROOT/backend" --tag "$API_IMAGE" --project "$PROJECT_ID"

echo "==> Deploying API service"
API_ENV_FILE="$TMP_DIR/api.env.yaml"
python3 - "$API_ENV_FILE" <<'PY'
import json
import os
import sys

path = sys.argv[1]

def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)

cors_raw = env("CORS_ORIGINS", "")
if cors_raw:
    try:
        cors_origins = json.loads(cors_raw)
    except json.JSONDecodeError:
        cors_origins = [s.strip() for s in cors_raw.strip("[]").split(",") if s.strip()]
else:
    cors_origins = ["https://www.kuberaiq.com", "https://kuberaiq.com", "https://api.kuberaiq.com"]

gcp_web = env("GCP_WEB_ORIGIN", "").strip()
if gcp_web and gcp_web not in cors_origins:
    cors_origins.append(gcp_web.rstrip("/"))

settings = {
    "ENVIRONMENT": env("ENVIRONMENT", "production"),
    "DATABASE_URL": env("DATABASE_URL"),
    "JWT_SECRET": env("JWT_SECRET"),
    "USE_MOCK_AUTH": env("USE_MOCK_AUTH", "false"),
    "USE_MOCK_LLM": env("USE_MOCK_LLM", "true"),
    "USE_MOCK_BLOB": env("USE_MOCK_BLOB", "true"),
    "USE_MOCK_WHATSAPP": env("USE_MOCK_WHATSAPP", "true"),
    "USE_MOCK_BILLING": env("USE_MOCK_BILLING", "false"),
    "CORS_ORIGINS": json.dumps(cors_origins),
    "GOOGLE_CLIENT_ID": env("GOOGLE_CLIENT_ID"),
    "GOOGLE_CLIENT_SECRET": env("GOOGLE_CLIENT_SECRET"),
    "GOOGLE_REDIRECT_URI": env("GOOGLE_REDIRECT_URI"),
    "ENTRA_TENANT_ID": env("ENTRA_TENANT_ID"),
    "ENTRA_CLIENT_ID": env("ENTRA_CLIENT_ID"),
    "ENTRA_CLIENT_SECRET": env("ENTRA_CLIENT_SECRET"),
    "NEXT_PUBLIC_OAUTH_COOKIE_DOMAIN": env("NEXT_PUBLIC_OAUTH_COOKIE_DOMAIN", ".kuberaiq.com"),
    "NEXT_PUBLIC_APEX_DOMAIN": env("NEXT_PUBLIC_APEX_DOMAIN", "kuberaiq.com"),
    "AZURE_OPENAI_ENDPOINT": env("AZURE_OPENAI_ENDPOINT"),
    "AZURE_OPENAI_API_KEY": env("AZURE_OPENAI_API_KEY"),
    "AZURE_OPENAI_DEPLOYMENT": env("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
    "AZURE_OPENAI_API_VERSION": env("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
    "AZURE_STORAGE_CONNECTION_STRING": env("AZURE_STORAGE_CONNECTION_STRING")
    if env("AZURE_STORAGE_CONNECTION_STRING", "").startswith("DefaultEndpointsProtocol=")
    and "AccountName=" in env("AZURE_STORAGE_CONNECTION_STRING", "")
    else "",
    "AZURE_STORAGE_CONTAINER": env("AZURE_STORAGE_CONTAINER", "invoices"),
    "WHATSAPP_PHONE_NUMBER_ID": env("WHATSAPP_PHONE_NUMBER_ID"),
    "WHATSAPP_ACCESS_TOKEN": env("WHATSAPP_ACCESS_TOKEN"),
    "WHATSAPP_VERIFY_TOKEN": env("WHATSAPP_VERIFY_TOKEN", "kuberaiq-verify"),
    "WHATSAPP_APP_SECRET": env("WHATSAPP_APP_SECRET"),
    "RAZORPAY_KEY_ID": env("RAZORPAY_KEY_ID"),
    "RAZORPAY_KEY_SECRET": env("RAZORPAY_KEY_SECRET"),
    "RAZORPAY_WEBHOOK_SECRET": env("RAZORPAY_WEBHOOK_SECRET"),
    "SUBSCRIPTION_PLAN_AMOUNT_PAISE": env("SUBSCRIPTION_PLAN_AMOUNT_PAISE", "99900"),
    "ADMIN_API_KEY": env("ADMIN_API_KEY"),
    "GUNICORN_BIND": "0.0.0.0:8000",
}

with open(path, "w", encoding="utf-8") as f:
    for k, v in settings.items():
        if v:
            f.write(f"{k}: \"{v.replace(chr(34), chr(92) + chr(34))}\"\n")
PY

gcloud run deploy "$API_SERVICE" \
  --image "$API_IMAGE" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --env-vars-file "$API_ENV_FILE" \
  "${CLOUDSQL_ANNOTATION[@]}" \
  --port 8000 \
  --cpu 1 \
  --memory 1Gi \
  --min-instances 0 \
  --max-instances 5

API_URL="$(gcloud run services describe "$API_SERVICE" --region "$REGION" --project "$PROJECT_ID" --format='value(status.url)')"
echo "API URL: $API_URL"

echo "==> Running database migrations"
cd "$ROOT/backend"
unset CORS_ORIGINS
MIGRATE_DATABASE_URL="$DATABASE_URL"
if [[ -n "${GCP_CLOUDSQL_CONNECTION_NAME:-}" && -n "${GCP_DB_PASSWORD:-}" ]]; then
  PUBLIC_IP="$(gcloud sql instances describe "${GCP_CLOUDSQL_INSTANCE:-}" --project "$PROJECT_ID" --format='value(ipAddresses[0].ipAddress)' 2>/dev/null || true)"
  if [[ -n "$PUBLIC_IP" ]]; then
    MYIP="$(curl -sf ifconfig.me 2>/dev/null || true)"
    if [[ -n "$MYIP" ]]; then
      gcloud sql instances patch "${GCP_CLOUDSQL_INSTANCE:-}" --project "$PROJECT_ID" \
        --authorized-networks="${MYIP}/32" --quiet >/dev/null 2>&1 || true
    fi
    MIGRATE_DATABASE_URL="postgresql+asyncpg://${GCP_DB_USER:-kuberaiq}:${GCP_DB_PASSWORD}@${PUBLIC_IP}:5432/${DB_NAME}"
  fi
fi
if ! DATABASE_URL="$MIGRATE_DATABASE_URL" alembic upgrade head; then
  echo "WARNING: Migration failed. Apps are deployed — retry:"
  echo "  cd backend && DATABASE_URL=... alembic upgrade head"
else
  CURRENT_REV="$(DATABASE_URL="$MIGRATE_DATABASE_URL" alembic current 2>/dev/null | awk '{print $1}' | head -1 || true)"
  echo "    Alembic at: ${CURRENT_REV:-unknown}"
fi
cd "$ROOT"

echo "==> Building and pushing Web image"
WEB_BUILD_URL="${WEB_URL_FOR_BUILD:-https://${WEB_SERVICE}-${REGION}.a.run.app}"
WEB_MOCK_AUTH="${USE_MOCK_AUTH:-false}"
WEB_MOCK_BILLING="${USE_MOCK_BILLING:-false}"
WEB_GOOGLE_REDIRECT="${GOOGLE_REDIRECT_URI:-https://www.kuberaiq.com/auth/callback}"
WEB_OAUTH_COOKIE_DOMAIN="${NEXT_PUBLIC_OAUTH_COOKIE_DOMAIN:-.kuberaiq.com}"
WEB_APEX_DOMAIN="${NEXT_PUBLIC_APEX_DOMAIN:-kuberaiq.com}"
WEB_BUILD_CONFIG="$TMP_DIR/cloudbuild-web.yaml"
WEB_BUILD_ARGS=(
  "build"
  "-f" "Dockerfile"
  "-t" "${WEB_IMAGE}"
  "--build-arg" "API_UPSTREAM_URL=${API_URL}"
  "--build-arg" "NEXT_PUBLIC_WEB_URL=${WEB_BUILD_URL}"
  "--build-arg" "NEXT_PUBLIC_USE_MOCK_AUTH=${WEB_MOCK_AUTH}"
  "--build-arg" "NEXT_PUBLIC_USE_MOCK_BILLING=${WEB_MOCK_BILLING}"
  "--build-arg" "NEXT_PUBLIC_GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID:-}"
  "--build-arg" "NEXT_PUBLIC_GOOGLE_REDIRECT_URI=${WEB_GOOGLE_REDIRECT}"
  "--build-arg" "NEXT_PUBLIC_OAUTH_COOKIE_DOMAIN=${WEB_OAUTH_COOKIE_DOMAIN}"
  "--build-arg" "NEXT_PUBLIC_APEX_DOMAIN=${WEB_APEX_DOMAIN}"
)
if [[ -n "${ENTRA_CLIENT_ID:-}" ]]; then
  WEB_BUILD_ARGS+=(
    "--build-arg" "NEXT_PUBLIC_ENTRA_CLIENT_ID=${ENTRA_CLIENT_ID}"
    "--build-arg" "NEXT_PUBLIC_ENTRA_TENANT_ID=${ENTRA_TENANT_ID:-common}"
    "--build-arg" "NEXT_PUBLIC_ENTRA_REDIRECT_URI=${ENTRA_REDIRECT_URI:-https://www.kuberaiq.com/auth/callback}"
  )
fi
{
  echo "steps:"
  echo "  - name: gcr.io/cloud-builders/docker"
  echo "    args:"
  for arg in "${WEB_BUILD_ARGS[@]}" "."; do
    echo "      - ${arg}"
  done
  echo "images:"
  echo "  - ${WEB_IMAGE}"
} >"$WEB_BUILD_CONFIG"

gcloud builds submit "$ROOT/frontend" \
  --project "$PROJECT_ID" \
  --config "$WEB_BUILD_CONFIG"

echo "==> Deploying Web service"
gcloud run deploy "$WEB_SERVICE" \
  --image "$WEB_IMAGE" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "HOSTNAME=0.0.0.0,API_UPSTREAM_URL=${API_URL},ADMIN_API_KEY=${ADMIN_API_KEY:-}" \
  --port 3000 \
  --cpu 1 \
  --memory 1Gi \
  --min-instances 0 \
  --max-instances 5

WEB_URL="$(gcloud run services describe "$WEB_SERVICE" --region "$REGION" --project "$PROJECT_ID" --format='value(status.url)')"
echo "WEB URL: $WEB_URL"

echo "==> Updating web service with canonical web URL"
gcloud run services update "$WEB_SERVICE" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --set-env-vars "HOSTNAME=0.0.0.0,API_UPSTREAM_URL=${API_URL},ADMIN_API_KEY=${ADMIN_API_KEY:-}" >/dev/null

echo "==> Smoke checks"
curl -sf "${API_URL}/health" >/dev/null
curl -sf "${API_URL}/health/ready" >/dev/null || true
curl -sf "${WEB_URL}" >/dev/null
if [[ "$USE_MOCK_AUTH" == "false" ]]; then
  MOCK_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${API_URL}/api/v1/auth/mock-login" \
    -H "Content-Type: application/json" -d '{"email":"qa@example.com"}')
  if [[ "$MOCK_STATUS" == "403" ]]; then
    echo "    mock-login disabled (403) — production auth mode OK"
  else
    echo "WARNING: Expected mock-login 403 when USE_MOCK_AUTH=false, got $MOCK_STATUS"
  fi
fi

echo ""
echo "GCP deployment complete."
echo "  API: ${API_URL}"
echo "  WEB: ${WEB_URL}"
echo ""
echo "Custom domains (www/api.kuberaiq.com):"
echo "  If DNS still points to Azure you will see 'Site Disabled' 403."
echo "  Fix: ./scripts/check-kuberaiq-dns-gcp.sh && ./scripts/setup-gcp-domains.sh"
echo "Azure remains unchanged."
