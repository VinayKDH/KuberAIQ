"""Recurring invoice template API tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_recurring_template_crud(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    cust = await client.post(
        "/api/v1/customers",
        headers=auth_headers,
        json={"name": "Monthly Subscriber", "phone": "9876512345"},
    )
    assert cust.status_code == 201
    customer_id = cust.json()["id"]

    create = await client.post(
        "/api/v1/invoices/recurring-templates",
        headers=auth_headers,
        json={
            "customer_id": customer_id,
            "name": "AMC Monthly",
            "frequency": "MONTHLY",
            "next_run_date": "2026-04-01",
            "items": [
                {
                    "description": "Maintenance fee",
                    "quantity": 1,
                    "unit": "NOS",
                    "unit_price": 1500,
                    "gst_rate": 18,
                }
            ],
        },
    )
    assert create.status_code == 201
    template = create.json()
    assert template["name"] == "AMC Monthly"
    assert template["is_active"] is True
    template_id = template["id"]

    listing = await client.get("/api/v1/invoices/recurring-templates", headers=auth_headers)
    assert listing.status_code == 200
    items = listing.json()["items"]
    assert any(row["id"] == template_id for row in items)

    updated = await client.patch(
        f"/api/v1/invoices/recurring-templates/{template_id}",
        headers=auth_headers,
        json={"is_active": False, "frequency": "WEEKLY"},
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["is_active"] is False
    assert body["frequency"] == "WEEKLY"
