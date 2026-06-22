"""API tests for product catalog."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_product_crud(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await client.post(
        "/api/v1/products",
        json={
            "name": "Widget A",
            "description": "Standard widget",
            "hsn_sac": "8471",
            "unit": "NOS",
            "default_price": "500.00",
            "gst_rate": "18",
        },
        headers=auth_headers,
    )
    assert created.status_code == 201
    product_id = created.json()["id"]

    listing = await client.get("/api/v1/products?q=Widget", headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1

    updated = await client.patch(
        f"/api/v1/products/{product_id}",
        json={"default_price": "550.00"},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["default_price"] == "550.00"

    deleted = await client.delete(f"/api/v1/products/{product_id}", headers=auth_headers)
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_hsn_lookup_by_code(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.get(
        "/api/v1/products/hsn-lookup",
        params={"hsn_sac": "0406"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["hsn_sac"] == "0406"
    assert body["gst_rate"] == "5"
    assert body["source"] == "catalog"


@pytest.mark.asyncio
async def test_hsn_lookup_by_name(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.get(
        "/api/v1/products/hsn-lookup",
        params={"name": "Paneer"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["hsn_sac"] == "0406"
    assert body["gst_rate"] == "5"
    assert body["source"] == "catalog"


@pytest.mark.asyncio
async def test_create_product_auto_gst_from_name(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await client.post(
        "/api/v1/products",
        json={
            "name": "Khoya",
            "default_price": "200.00",
        },
        headers=auth_headers,
    )
    assert created.status_code == 201
    body = created.json()
    assert body["hsn_sac"] == "0402"
    assert body["gst_rate"] == "5"


@pytest.mark.asyncio
async def test_create_product_with_initial_stock(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await client.post(
        "/api/v1/products",
        json={
            "name": "Stocked Widget",
            "default_price": "100.00",
            "gst_rate": "18",
            "stock_qty": "50",
        },
        headers=auth_headers,
    )
    assert created.status_code == 201
    assert created.json()["stock_qty"] == "50"


@pytest.mark.asyncio
async def test_adjust_stock_delta(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await client.post(
        "/api/v1/products",
        json={
            "name": "Adjustable Item",
            "default_price": "25.00",
            "gst_rate": "5",
            "stock_qty": "10",
        },
        headers=auth_headers,
    )
    product_id = created.json()["id"]

    adjusted = await client.post(
        f"/api/v1/products/{product_id}/stock",
        json={"delta": "15", "reason": "Purchase"},
        headers=auth_headers,
    )
    assert adjusted.status_code == 200
    assert float(adjusted.json()["stock_qty"]) == pytest.approx(25)

    decremented = await client.post(
        f"/api/v1/products/{product_id}/stock",
        json={"delta": "-5", "reason": "Damaged / expired"},
        headers=auth_headers,
    )
    assert decremented.status_code == 200
    assert float(decremented.json()["stock_qty"]) == pytest.approx(20)


@pytest.mark.asyncio
async def test_adjust_stock_absolute_qty(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await client.post(
        "/api/v1/products",
        json={
            "name": "Set Qty Item",
            "default_price": "10.00",
            "gst_rate": "0",
            "stock_qty": "8",
        },
        headers=auth_headers,
    )
    product_id = created.json()["id"]

    response = await client.post(
        f"/api/v1/products/{product_id}/stock",
        json={"qty": "100", "reason": "Opening stock"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["stock_qty"] == "100"


@pytest.mark.asyncio
async def test_adjust_stock_rejects_negative_result(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await client.post(
        "/api/v1/products",
        json={
            "name": "Low Item",
            "default_price": "10.00",
            "gst_rate": "0",
            "stock_qty": "3",
        },
        headers=auth_headers,
    )
    product_id = created.json()["id"]

    response = await client.post(
        f"/api/v1/products/{product_id}/stock",
        json={"delta": "-10", "reason": "Stock correction"},
        headers=auth_headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_adjust_stock_invalid_reason(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await client.post(
        "/api/v1/products",
        json={"name": "Reason Test", "default_price": "10.00"},
        headers=auth_headers,
    )
    product_id = created.json()["id"]

    response = await client.post(
        f"/api/v1/products/{product_id}/stock",
        json={"delta": "1", "reason": "Invalid reason"},
        headers=auth_headers,
    )
    assert response.status_code == 422
