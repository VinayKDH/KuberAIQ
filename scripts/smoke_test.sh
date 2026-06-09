#!/usr/bin/env bash
# End-to-end API smoke test for local KuberAIQ stack.
set -euo pipefail

BASE="${BASE_URL:-http://localhost:8000}"
DEMO_EMAIL="${DEMO_EMAIL:-owner@demo.kuberaiq.com}"
UNIQUE_PHONE=$(python3 -c "import random; print(f'9{random.randint(100000000, 999999999)}')")

echo "==> Health"
curl -sf "$BASE/health" | grep -q '"status":"ok"'
curl -sf "$BASE/health/ready" | grep -q '"database":"ok"'

echo "==> Mock login"
TOKEN=$(curl -sf -X POST "$BASE/api/v1/auth/mock-login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$DEMO_EMAIL\"}" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
AUTH="Authorization: Bearer $TOKEN"

echo "==> Auth me"
curl -sf "$BASE/api/v1/auth/me" -H "$AUTH" | grep -q "$DEMO_EMAIL"

echo "==> Create customer"
CUST=$(curl -sf -X POST "$BASE/api/v1/customers" -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"name\":\"Smoke Test Traders\",\"phone\":\"$UNIQUE_PHONE\",\"gstin\":\"27AAPFU0939F1ZV\"}")
CID=$(echo "$CUST" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "==> Create invoice"
INV=$(curl -sf -X POST "$BASE/api/v1/invoices" -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"customer_id\":\"$CID\",\"issue_date\":\"2026-06-06\",\"due_date\":\"2026-06-21\",\"status\":\"ISSUED\",\"items\":[{\"description\":\"Cement\",\"quantity\":10,\"unit_price\":350,\"gst_rate\":18}]}")
IID=$(echo "$INV" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "==> Record payment"
curl -sf -X POST "$BASE/api/v1/invoices/$IID/payments" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"amount":1000,"paid_on":"2026-06-10","method":"UPI"}' | grep -q '"amount"'

echo "==> Dashboard"
curl -sf "$BASE/api/v1/dashboard?from=2026-04-01&to=2026-06-30" -H "$AUTH" | grep -q '"revenue"'

echo "==> Collections overdue"
curl -sf "$BASE/api/v1/collections/overdue" -H "$AUTH" | grep -q '"items"'

echo "==> AI chat"
curl -sf -X POST "$BASE/api/v1/ai/chat" -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"message":"How much money is pending?"}' | grep -q '"message"'

echo ""
echo "All smoke tests passed."
