"""API health endpoint tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_live(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_health_metrics(client: AsyncClient) -> None:
    metrics = await client.get("/health/metrics")
    assert metrics.status_code == 200
    body = metrics.json()
    assert "requests_total" in body
    assert body["requests_total"] >= 1


@pytest.mark.asyncio
async def test_health_integrations(client: AsyncClient) -> None:
    response = await client.get("/health/integrations")
    assert response.status_code == 200
    body = response.json()
    assert body["auth_mode"] in {"mock", "oauth"}
    assert body["llm_mode"] in {"mock", "live"}
    assert body["whatsapp_mode"] in {"mock", "live"}


@pytest.mark.asyncio
async def test_security_headers(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert response.headers.get("Content-Security-Policy")
