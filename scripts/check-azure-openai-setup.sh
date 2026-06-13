#!/usr/bin/env bash
# Verify Azure OpenAI configuration for KuberAIQ AI copilot.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/.env.prod}"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  set -a && source "$ENV_FILE" && set +a
fi

API_BASE="${API_BASE:-${PUBLIC_API_URL:-https://api.kuberaiq.com}}"

echo "=== KuberAIQ Azure OpenAI setup check ==="
echo "API base: $API_BASE"
echo ""

missing=0
for var in AZURE_OPENAI_ENDPOINT AZURE_OPENAI_API_KEY AZURE_OPENAI_DEPLOYMENT; do
  if [[ -z "${!var:-}" ]]; then
    echo "✗ $var is not set"
    missing=1
  else
    echo "✓ $var is set"
  fi
done

echo "  API version: ${AZURE_OPENAI_API_VERSION:-2024-08-01-preview}"
echo ""

if [[ "$missing" -eq 0 ]]; then
  echo "Endpoint probe (deployment list not required):"
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 \
    -H "api-key: ${AZURE_OPENAI_API_KEY}" \
    "${AZURE_OPENAI_ENDPOINT%/}/openai/deployments?api-version=${AZURE_OPENAI_API_VERSION:-2024-08-01-preview}" || echo "000")
  if [[ "$HTTP_CODE" =~ ^(200|401|403)$ ]]; then
    echo "✓ Azure OpenAI endpoint reachable (HTTP $HTTP_CODE)"
  else
    echo "⚠ Azure OpenAI endpoint returned HTTP $HTTP_CODE — check endpoint URL and key"
  fi
  echo ""
fi

echo "Health integrations:"
curl -fsS "${API_BASE}/health/integrations" | python3 -m json.tool 2>/dev/null || curl -fsS "${API_BASE}/health/integrations"
echo ""

echo "Azure Portal:"
echo "  1. Create Azure OpenAI resource + deploy model (e.g. gpt-4o)"
echo "  2. Copy endpoint + key → AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY"
echo "  3. Set AZURE_OPENAI_DEPLOYMENT to your deployment name"
echo "  4. Set USE_MOCK_LLM=false (or leave unset — deploy auto-disables mock when creds present)"
echo "  5. Redeploy API: ENV_FILE=$ENV_FILE ./scripts/deploy-prod.sh"
echo ""

if [[ "$missing" -eq 1 ]]; then
  exit 1
fi
