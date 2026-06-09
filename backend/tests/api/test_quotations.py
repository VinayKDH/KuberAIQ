"""API tests for quotations workflow."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _create_customer(client: AsyncClient, headers: dict[str, str]) -> str:
    resp = await client.post(
        "/api/v1/customers",
        json={"name": "Quote Customer", "phone": "9876543210"},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_quotation_convert_to_invoice(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    customer_id = await _create_customer(client, auth_headers)
    created = await client.post(
        "/api/v1/quotations",
        json={
            "customer_id": customer_id,
            "issue_date": "2026-06-01",
            "valid_until": "2026-06-15",
            "items": [
                {
                    "description": "Consulting",
                    "quantity": "1",
                    "unit_price": "10000",
                    "gst_rate": "18",
                    "unit": "NOS",
                }
            ],
        },
        headers=auth_headers,
    )
    assert created.status_code == 201
    quotation_id = created.json()["id"]
    assert created.json()["quotation_number"] is not None

    sent = await client.post(
        f"/api/v1/quotations/{quotation_id}:send",
        headers=auth_headers,
    )
    assert sent.status_code == 200
    assert sent.json()["status"] == "SENT"

    converted = await client.post(
        f"/api/v1/quotations/{quotation_id}:convert",
        headers=auth_headers,
    )
    assert converted.status_code == 200
    assert converted.json()["invoice_id"]
    assert converted.json()["quotation"]["status"] == "CONVERTED"
