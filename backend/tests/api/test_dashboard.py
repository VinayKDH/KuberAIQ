"""Dashboard API integration tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_summary(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.get(
        "/api/v1/dashboard?from=2026-04-01&to=2026-06-30",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "revenue" in data
    assert "pending" in data
    assert "overdue" in data
    assert "aging" in data
    assert "cashflow" in data
    assert "cashflow_forecast" in data
    assert "cashflow_alert" in data
    assert "top_products" in data


@pytest.mark.asyncio
async def test_dashboard_cashflow_includes_open_invoices(
    client: AsyncClient, auth_headers: dict
) -> None:
    cust = await client.post(
        "/api/v1/customers",
        json={"name": "Cashflow Co", "phone": "9000012345"},
        headers=auth_headers,
    )
    customer_id = cust.json()["id"]
    await client.post(
        "/api/v1/invoices",
        json={
            "customer_id": customer_id,
            "issue_date": "2026-06-01",
            "due_date": "2026-07-15",
            "status": "ISSUED",
            "items": [{"description": "Goods", "quantity": 1, "unit_price": 5000, "gst_rate": 18}],
        },
        headers=auth_headers,
    )
    resp = await client.get(
        "/api/v1/dashboard?from=2026-04-01&to=2026-06-30",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    cashflow = resp.json()["cashflow"]
    assert len(cashflow) >= 1
    assert cashflow[0]["expected_inflow"] > 0
