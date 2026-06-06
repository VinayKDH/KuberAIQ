"""End-to-end smoke flow via pytest (mirrors scripts/smoke_test.sh)."""
from __future__ import annotations

import random

import pytest
from httpx import AsyncClient

from app.core.constants import DEMO_USER_EMAIL


@pytest.mark.asyncio
async def test_full_business_flow(client: AsyncClient) -> None:
    login = await client.post("/api/v1/auth/mock-login", json={"email": DEMO_USER_EMAIL})
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    phone = f"9{random.randint(100000000, 999999999)}"
    cust = await client.post(
        "/api/v1/customers",
        json={"name": "E2E Traders", "phone": phone},
        headers=headers,
    )
    assert cust.status_code == 201
    customer_id = cust.json()["id"]

    inv = await client.post(
        "/api/v1/invoices",
        json={
            "customer_id": customer_id,
            "issue_date": "2026-06-06",
            "due_date": "2026-06-21",
            "status": "ISSUED",
            "items": [{"description": "Goods", "quantity": 2, "unit_price": 500, "gst_rate": 18}],
        },
        headers=headers,
    )
    assert inv.status_code == 201
    invoice_id = inv.json()["id"]

    pay = await client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        json={"amount": 500, "paid_on": "2026-06-10", "method": "CASH"},
        headers=headers,
    )
    assert pay.status_code == 201

    dash = await client.get(
        "/api/v1/dashboard?from=2026-04-01&to=2026-06-30",
        headers=headers,
    )
    assert dash.status_code == 200

    ai = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Show unpaid invoices"},
        headers=headers,
    )
    assert ai.status_code == 200
