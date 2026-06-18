#!/usr/bin/env bash
# Provision KuberAIQ database on existing GCP Cloud SQL (creates DB + user, runs migrations).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/.env.gcp}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Copy .env.gcp.example to .env.gcp and fill values." >&2
  exit 1
fi

# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
INSTANCE="${GCP_CLOUDSQL_INSTANCE:-bf-postgres}"
REGION="${GCP_REGION:-asia-south1}"
DB_NAME="${KUBERAIQ_DB_NAME:-kuberaiq}"
DB_USER="${GCP_DB_USER:-kuberaiq}"
DB_PASSWORD="${GCP_DB_PASSWORD:-}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "GCP_PROJECT_ID is required." >&2
  exit 1
fi

if [[ -z "$DB_PASSWORD" ]]; then
  DB_PASSWORD="$(openssl rand -base64 24 | tr -dc 'A-Za-z0-9' | head -c 24)"
  echo "Generated GCP_DB_PASSWORD=$DB_PASSWORD"
fi

CONN="${GCP_CLOUDSQL_CONNECTION_NAME:-${PROJECT_ID}:${REGION}:${INSTANCE}}"

gcloud sql databases describe "$DB_NAME" --instance="$INSTANCE" --project="$PROJECT_ID" >/dev/null 2>&1 \
  || gcloud sql databases create "$DB_NAME" --instance="$INSTANCE" --project="$PROJECT_ID"

if gcloud sql users list --instance="$INSTANCE" --project="$PROJECT_ID" --format='value(name)' | rg -qx "$DB_USER"; then
  gcloud sql users set-password "$DB_USER" --instance="$INSTANCE" --project="$PROJECT_ID" --password="$DB_PASSWORD"
else
  gcloud sql users create "$DB_USER" --instance="$INSTANCE" --project="$PROJECT_ID" --password="$DB_PASSWORD"
fi

PUBLIC_IP="$(gcloud sql instances describe "$INSTANCE" --project="$PROJECT_ID" --format='value(ipAddresses[0].ipAddress)')"
MYIP="$(curl -sf ifconfig.me)"
gcloud sql instances patch "$INSTANCE" --project="$PROJECT_ID" \
  --authorized-networks="${MYIP}/32" --quiet

MIGRATE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${PUBLIC_IP}:5432/${DB_NAME}"
echo "==> Running Alembic migrations"
cd "$ROOT/backend"
unset CORS_ORIGINS
DATABASE_URL="$MIGRATE_URL" alembic upgrade head

SOCKET_URL="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@localhost/${DB_NAME}?host=/cloudsql/${CONN}"
echo ""
echo "Provision complete."
echo "  Connection: $CONN"
echo "  Cloud Run DATABASE_URL:"
echo "    $SOCKET_URL"
echo ""
echo "Add to .env.gcp:"
echo "  GCP_DB_PASSWORD=$DB_PASSWORD"
echo "  DATABASE_URL=$SOCKET_URL"
