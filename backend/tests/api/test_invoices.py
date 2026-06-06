"""Invoice API integration tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_list_invoice(client: AsyncClient, auth_headers: dict) -> None:
    cust = await client.post(
        "/api/v1/customers",
        json={"name": "ABC Traders", "phone": "9876543210"},
        headers=auth_headers,
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
            "items": [
                {
                    "description": "OPC 53 Grade Cement",
                    "hsn_sac": "2523",
                    "quantity": 50,
                    "unit": "BAG",
                    "unit_price": 350.0,
                    "gst_rate": 18,
                }
            ],
        },
        headers=auth_headers,
    )
    assert inv.status_code == 201
    body = inv.json()
    assert body["status"] == "ISSUED"
    assert float(body["grand_total"]) == 20650.0
    assert body["invoice_number"] is not None

    listing = await client.get("/api/v1/invoices?status=ISSUED", headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1


@pytest.mark.asyncio
async def test_record_payment(client: AsyncClient, auth_headers: dict) -> None:
    cust = await client.post(
        "/api/v1/customers",
        json={"name": "Pay Test Co", "phone": "9123456789"},
        headers=auth_headers,
    )
    customer_id = cust.json()["id"]
    inv = await client.post(
        "/api/v1/invoices",
        json={
            "customer_id": customer_id,
            "issue_date": "2026-06-06",
            "due_date": "2026-06-21",
            "status": "ISSUED",
            "items": [
                {
                    "description": "Item",
                    "quantity": 1,
                    "unit_price": 1000.0,
                    "gst_rate": 18,
                }
            ],
        },
        headers=auth_headers,
    )
    invoice_id = inv.json()["id"]
    pay = await client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        json={"amount": 590.0, "paid_on": "2026-06-10", "method": "UPI"},
        headers=auth_headers,
    )
    assert pay.status_code == 201
    assert float(pay.json()["amount"]) == 590.0
