"""Invoice lifecycle API tests."""
from __future__ import annotations

import random

import pytest
from httpx import AsyncClient


async def _create_issued_invoice(client: AsyncClient, headers: dict) -> str:
    phone = f"9{random.randint(100000000, 999999999)}"
    cust = await client.post(
        "/api/v1/customers",
        json={"name": "Lifecycle Co", "phone": phone},
        headers=headers,
    )
    customer_id = cust.json()["id"]
    inv = await client.post(
        "/api/v1/invoices",
        json={
            "customer_id": customer_id,
            "issue_date": "2026-06-06",
            "due_date": "2026-06-21",
            "status": "DRAFT",
            "items": [{"description": "Service", "quantity": 1, "unit_price": 1000, "gst_rate": 18}],
        },
        headers=headers,
    )
    return inv.json()["id"]


@pytest.mark.asyncio
async def test_get_and_cancel_draft_invoice(client: AsyncClient, auth_headers: dict) -> None:
    invoice_id = await _create_issued_invoice(client, auth_headers)

    get_resp = await client.get(f"/api/v1/invoices/{invoice_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "DRAFT"

    cancel = await client.post(
        f"/api/v1/invoices/{invoice_id}:cancel",
        json={"reason": "Customer cancelled order"},
        headers=auth_headers,
    )
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_issue_draft_invoice(client: AsyncClient, auth_headers: dict) -> None:
    invoice_id = await _create_issued_invoice(client, auth_headers)
    issued = await client.post(f"/api/v1/invoices/{invoice_id}:issue", headers=auth_headers)
    assert issued.status_code == 200
    body = issued.json()
    assert body["status"] == "ISSUED"
    assert body["invoice_number"] is not None
