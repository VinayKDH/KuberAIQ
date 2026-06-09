"""Compliance API integration tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_compliance_dashboard(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.get("/api/v1/compliance/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "deadlines" in data
    assert "e_invoice" in data
    assert "checklist" in data
    assert data["e_invoice"]["threshold"] == 1000000.0


@pytest.mark.asyncio
async def test_register_invoice_irn(client: AsyncClient, auth_headers: dict) -> None:
    cust = await client.post(
        "/api/v1/customers",
        json={"name": "IRN Co", "phone": "9000098765", "billing_address": "Pune"},
        headers=auth_headers,
    )
    inv = await client.post(
        "/api/v1/invoices",
        json={
            "customer_id": cust.json()["id"],
            "issue_date": "2026-06-01",
            "due_date": "2026-06-15",
            "status": "ISSUED",
            "items": [{"description": "Steel rods", "quantity": 10, "unit_price": 500, "gst_rate": 18}],
        },
        headers=auth_headers,
    )
    invoice_id = inv.json()["id"]
    resp = await client.post(
        f"/api/v1/invoices/{invoice_id}/irn",
        json={"irn": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["irn"] == "A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6"
