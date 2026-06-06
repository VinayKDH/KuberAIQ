"""Customer lifecycle API tests."""
from __future__ import annotations

import random

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_customer_crud_and_history(client: AsyncClient, auth_headers: dict) -> None:
    phone = f"9{random.randint(100000000, 999999999)}"
    create = await client.post(
        "/api/v1/customers",
        json={"name": "History Co", "phone": phone, "email": "history@example.com"},
        headers=auth_headers,
    )
    assert create.status_code == 201
    customer_id = create.json()["id"]

    get_one = await client.get(f"/api/v1/customers/{customer_id}", headers=auth_headers)
    assert get_one.status_code == 200

    patch = await client.patch(
        f"/api/v1/customers/{customer_id}",
        json={"name": "History Co Updated"},
        headers=auth_headers,
    )
    assert patch.status_code == 200
    assert patch.json()["name"] == "History Co Updated"

    history = await client.get(f"/api/v1/customers/{customer_id}/history", headers=auth_headers)
    assert history.status_code == 200
    assert "outstanding" in history.json()

    delete = await client.delete(f"/api/v1/customers/{customer_id}", headers=auth_headers)
    assert delete.status_code == 204
