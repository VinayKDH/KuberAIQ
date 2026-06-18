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
