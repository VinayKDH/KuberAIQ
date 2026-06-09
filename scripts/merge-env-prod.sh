#!/usr/bin/env bash
# Merge Azure prod resource names from .env.prod.generated into .env.prod (keeps existing secrets).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GENERATED="${GENERATED:-$ROOT/.env.prod.generated}"
TARGET="${TARGET:-$ROOT/.env.prod}"

if [[ ! -f "$GENERATED" ]]; then
  echo "Run ./scripts/provision-prod.sh first to create $GENERATED" >&2
  exit 1
fi
if [[ ! -f "$TARGET" ]]; then
  cp "$ROOT/.env.prod.example" "$TARGET"
fi

RG=$(grep '^AZURE_RESOURCE_GROUP=' "$GENERATED" | cut -d= -f2-)
STORAGE_NAME=$(az storage account list -g "$RG" --query "[0].name" -o tsv 2>/dev/null || true)
KV_NAME=$(az keyvault list -g "$RG" --query "[0].name" -o tsv 2>/dev/null || true)

export MERGE_GENERATED="$GENERATED"
export MERGE_TARGET="$TARGET"
export MERGE_STORAGE_CS=""
export MERGE_KV_NAME="$KV_NAME"
if [[ -n "$STORAGE_NAME" ]]; then
  MERGE_STORAGE_CS=$(az storage account show-connection-string -g "$RG" -n "$STORAGE_NAME" -o tsv)
  export MERGE_STORAGE_CS
fi

python3 <<'PY'
import os
from pathlib import Path

generated = Path(os.environ["MERGE_GENERATED"])
target = Path(os.environ["MERGE_TARGET"])
updates = {}
for line in generated.read_text().splitlines():
    if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    updates[k] = v

storage_cs = os.environ.get("MERGE_STORAGE_CS", "")
if storage_cs:
    updates["AZURE_STORAGE_CONNECTION_STRING"] = storage_cs
kv = os.environ.get("MERGE_KV_NAME", "")
if kv:
    updates["AZURE_KEY_VAULT"] = kv
updates["CORS_ORIGINS"] = (
    '["https://www.kuberaiq.com","https://kuberaiq.com","https://api.kuberaiq.com",'
    '"https://kuberaiq-web-prod.azurewebsites.net"]'
)
updates["WHATSAPP_VERIFY_TOKEN"] = "kuberaiq-verify"

lines = target.read_text().splitlines()
seen = set()
out = []
for line in lines:
    if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
        out.append(line)
        continue
    key = line.split("=", 1)[0]
    if key in updates and updates[key] and not updates[key].startswith("<"):
        out.append(f"{key}={updates[key]}")
        seen.add(key)
    else:
        out.append(line)
for key, val in updates.items():
    if key not in seen and val and not val.startswith("<"):
        out.append(f"{key}={val}")
target.write_text("\n".join(out) + "\n")
print(f"Merged {len(updates)} keys into {target}")
PY

echo "Ensure POSTGRES_ADMIN_PASSWORD is set (provision console or reset via Azure CLI)."
