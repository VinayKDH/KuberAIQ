"""Dashboard API integration tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_summary(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.get(
        "/api/v1/dashboard?from=2026-04-01&to=2026-06-30",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "revenue" in data
    assert "pending" in data
    assert "overdue" in data
    assert "aging" in data
    assert "cashflow" in data
