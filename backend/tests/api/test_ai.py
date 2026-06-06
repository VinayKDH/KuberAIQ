"""AI copilot API integration tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ai_chat_unpaid_invoices(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Show unpaid invoices"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "message" in body
    assert "intent" in body


@pytest.mark.asyncio
async def test_ai_chat_pending_amount(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.post(
        "/api/v1/ai/chat",
        json={"message": "How much money is pending?"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["message"]
