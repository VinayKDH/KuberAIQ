#!/usr/bin/env bash
# Deploy to App Services that Hostinger DNS currently points at (legacy rg-vyaparai-dev).
# Use until www/api CNAMEs target kuberaiq-*-prod.azurewebsites.net.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../infra/azure/naming.sh
source "$ROOT/infra/azure/naming.sh"

LIVE_ENV="$ROOT/.env.live-dns"
PROD_ENV="${ENV_FILE:-$ROOT/.env.prod}"

if [[ ! -f "$PROD_ENV" ]]; then
  echo "Missing $PROD_ENV" >&2
  exit 1
fi

python3 - "$PROD_ENV" "$LIVE_ENV" <<'PY'
import sys
from pathlib import Path

prod = Path(sys.argv[1])
live = Path(sys.argv[2])
overrides = {
    "AZURE_RESOURCE_GROUP": "rg-vyaparai-dev",
    "AZURE_ACR": "vyaparaitqjbqun57v",
    "AZURE_API_APP_NAME": "vyaparai-api-dev",
    "AZURE_WEB_APP_NAME": "vyaparai-dev",
    "AZURE_WEB_HOSTNAME": "vyaparai-dev.azurewebsites.net",
    "AZURE_API_HOSTNAME": "vyaparai-api-dev.azurewebsites.net",
    "AZURE_KEY_VAULT": "kv-vyapar-tqjbqun5",
    "AZURE_POSTGRES_FQDN": "vyaparai-pg-tqjbqun57vvae.postgres.database.azure.com",
    "POSTGRES_ADMIN_LOGIN": "vyaparaiadmin",
    "AZURE_STORAGE_CONNECTION_STRING": "",  # filled below if possible
}
lines = prod.read_text().splitlines()
seen = set()
out = []
for line in lines:
    if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
        out.append(line)
        continue
    key = line.split("=", 1)[0]
    if key in overrides:
        val = overrides[key]
        if val:
            out.append(f"{key}={val}")
        seen.add(key)
    else:
        out.append(line)
for key, val in overrides.items():
    if key not in seen and val:
        out.append(f"{key}={val}")
live.write_text("\n".join(out) + "\n")
PY

# Legacy Postgres password (prod .env may have been rotated for new server)
if grep -q '^POSTGRES_ADMIN_PASSWORD=' "$PROD_ENV" && \
   grep '^AZURE_POSTGRES_FQDN=vyaparai-pg' "$LIVE_ENV" >/dev/null 2>&1; then
  LEGACY_PW="hjB6OE7cp4ZqYOH5viSNAKaf"
  if [[ -f "$ROOT/.env.azure" ]]; then
    LEGACY_PW=$(grep '^POSTGRES_ADMIN_PASSWORD=' "$ROOT/.env.azure" | cut -d= -f2- || echo "$LEGACY_PW")
  fi
  sed -i '' "s/^POSTGRES_ADMIN_PASSWORD=.*/POSTGRES_ADMIN_PASSWORD=${LEGACY_PW}/" "$LIVE_ENV"
fi

STORAGE_CS=$(az storage account show-connection-string -g rg-vyaparai-dev -n vyaparaitqjbqun57vvae -o tsv 2>/dev/null || true)
if [[ -n "$STORAGE_CS" ]]; then
  python3 - "$LIVE_ENV" "$STORAGE_CS" <<'PY'
import sys
from pathlib import Path
path = Path(sys.argv[1])
cs = sys.argv[2]
lines = path.read_text().splitlines()
out = []
done = False
for line in lines:
    if line.startswith("AZURE_STORAGE_CONNECTION_STRING="):
        out.append(f"AZURE_STORAGE_CONNECTION_STRING={cs}")
        done = True
    else:
        out.append(line)
if not done:
    out.append(f"AZURE_STORAGE_CONNECTION_STRING={cs}")
path.write_text("\n".join(out) + "\n")
PY
fi

echo "==> Live DNS deploy → vyaparai-dev / vyaparai-api-dev"
ENV_FILE="$LIVE_ENV" exec "$ROOT/scripts/deploy-prod.sh"
