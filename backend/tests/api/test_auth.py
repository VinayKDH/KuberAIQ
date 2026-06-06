"""Auth API integration tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.constants import DEMO_USER_EMAIL


@pytest.mark.asyncio
async def test_mock_login_and_me(client: AsyncClient) -> None:
    login = await client.post(
        "/api/v1/auth/mock-login",
        json={"email": DEMO_USER_EMAIL},
    )
    assert login.status_code == 200
    body = login.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == DEMO_USER_EMAIL

    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["user"]["role"] == "OWNER"


@pytest.mark.asyncio
async def test_mock_login_unknown_user(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/mock-login",
        json={"email": "unknown@example.com"},
    )
    assert resp.status_code == 404
