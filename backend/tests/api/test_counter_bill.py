"""Counter billing API tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _create_product(client: AsyncClient, auth_headers: dict[str, str]) -> str:
    created = await client.post(
        "/api/v1/products",
        json={
            "name": "Counter Rice 1kg",
            "default_price": "80.00",
            "gst_rate": "5",
            "stock_qty": "100",
            "unit": "KG",
        },
        headers=auth_headers,
    )
    assert created.status_code == 201
    return created.json()["id"]


@pytest.mark.asyncio
async def test_counter_bill_issues_invoice(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    product_id = await _create_product(client, auth_headers)

    response = await client.post(
        "/api/v1/invoices/counter",
        json={
            "product_id": product_id,
            "quantity": "2",
            "customer_name": "Ram Kumar",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    body = response.json()
    invoice = body["invoice"]
    assert invoice["status"] == "ISSUED"
    assert invoice["invoice_number"] is not None
    assert body["customer_name"] == "Ram Kumar"
    assert float(invoice["grand_total"]) == pytest.approx(168.0, rel=1e-3)

    listing = await client.get("/api/v1/invoices?status=ISSUED", headers=auth_headers)
    assert listing.status_code == 200
    ids = {item["id"] for item in listing.json()["items"]}
    assert invoice["id"] in ids


@pytest.mark.asyncio
async def test_counter_bill_walk_in_customer(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    product_id = await _create_product(client, auth_headers)

    response = await client.post(
        "/api/v1/invoices/counter",
        json={"product_id": product_id, "quantity": 1},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["customer_name"] == "Walk-in Customer"


@pytest.mark.asyncio
async def test_counter_bill_low_stock_warning(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await client.post(
        "/api/v1/products",
        json={
            "name": "Low Stock Item",
            "default_price": "10.00",
            "gst_rate": "0",
            "stock_qty": "5",
        },
        headers=auth_headers,
    )
    product_id = created.json()["id"]

    response = await client.post(
        "/api/v1/invoices/counter",
        json={"product_id": product_id, "quantity": 1},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["stock_warning"] is not None


@pytest.mark.asyncio
async def test_counter_bill_invalid_quantity(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    product_id = await _create_product(client, auth_headers)

    response = await client.post(
        "/api/v1/invoices/counter",
        json={"product_id": product_id, "quantity": 0},
        headers=auth_headers,
    )
    assert response.status_code == 422
