#!/usr/bin/env bash
# Lightweight API load smoke test (Sprint 5 observability check).
set -euo pipefail

BASE="${1:-http://localhost:8000}"
REQUESTS="${2:-50}"

echo "Load testing $BASE/health ($REQUESTS requests)..."
ok=0
for _ in $(seq 1 "$REQUESTS"); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/health")
  if [[ "$code" == "200" ]]; then ok=$((ok + 1)); fi
done
echo "Success: $ok/$REQUESTS"
metrics=$(curl -s "$BASE/health/metrics")
echo "Metrics: $metrics"
