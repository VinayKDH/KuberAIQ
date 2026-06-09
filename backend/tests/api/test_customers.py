"""Customer API tests."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_create_and_list_customer(client, auth_headers):
    create_resp = await client.post(
        "/api/v1/customers",
        json={
            "name": "ABC Traders",
            "phone": "9876543210",
            "email": "abc@traders.in",
            "gstin": "27AAPFU0939F1ZV",
            "billing_address": "MIDC, Pune",
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["name"] == "ABC Traders"
    assert body["phone"] == "9876543210"
    assert body["state_code"] == "27"
    assert body["gstin"] == "27AAPFU0939F1ZV"

    list_resp = await client.get("/api/v1/customers?q=ABC", headers=auth_headers)
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] >= 1
    assert any(c["name"] == "ABC Traders" for c in data["items"])


@pytest.mark.asyncio
async def test_create_customer_requires_auth(client):
    response = await client.post(
        "/api/v1/customers",
        json={"name": "Test", "phone": "9876543210"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_customer_statement_pdf(client, auth_headers):
    create_resp = await client.post(
        "/api/v1/customers",
        json={"name": "Statement Co", "phone": "9876501234"},
        headers=auth_headers,
    )
    customer_id = create_resp.json()["id"]
    await client.post(
        "/api/v1/invoices",
        json={
            "customer_id": customer_id,
            "issue_date": "2026-06-01",
            "due_date": "2026-06-15",
            "status": "ISSUED",
            "items": [{"description": "Goods", "quantity": 1, "unit_price": 1000, "gst_rate": 18}],
        },
        headers=auth_headers,
    )

    resp = await client.get(
        f"/api/v1/customers/{customer_id}/statement.pdf",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:4] == b"%PDF"
