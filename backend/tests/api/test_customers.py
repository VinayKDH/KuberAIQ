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
