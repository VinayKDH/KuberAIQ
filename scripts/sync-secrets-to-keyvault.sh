#!/usr/bin/env bash
set -euo pipefail

KEYVAULT_NAME="${1:-}"
ENV_FILE="${2:-.env.prod}"

if [[ -z "$KEYVAULT_NAME" ]]; then
  echo "Usage: $0 <keyvault-name> [env-file]" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

declare -a KEYS=(
  JWT_SECRET
  AZURE_OPENAI_API_KEY
  AZURE_STORAGE_CONNECTION_STRING
  WHATSAPP_ACCESS_TOKEN
  WHATSAPP_APP_SECRET
  RAZORPAY_KEY_ID
  RAZORPAY_KEY_SECRET
  RAZORPAY_WEBHOOK_SECRET
  ADMIN_API_KEY
)

for key in "${KEYS[@]}"; do
  value="${!key:-}"
  if [[ -n "$value" ]]; then
    az keyvault secret set --vault-name "$KEYVAULT_NAME" --name "$key" --value "$value" >/dev/null
    echo "Synced $key"
  fi
done

echo "Secret sync complete."
