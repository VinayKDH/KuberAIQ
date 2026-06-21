"""Admin portal API tests."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.startup.seed import DEMO_COMPANY_ID

ADMIN_KEY = "test-admin-key-secret"


@pytest.fixture(autouse=True)
def admin_api_key(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", ADMIN_KEY)
    monkeypatch.setattr("app.api.deps.settings.admin_api_key", ADMIN_KEY)
    from app.core import config as config_mod

    config_mod.get_settings.cache_clear()
    yield
    config_mod.get_settings.cache_clear()


def admin_headers() -> dict[str, str]:
    return {"X-Admin-Api-Key": ADMIN_KEY}


@pytest.mark.asyncio
async def test_admin_auth_verify(client: AsyncClient) -> None:
    response = await client.post("/api/v1/admin/auth/verify", headers=admin_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True


@pytest.mark.asyncio
async def test_admin_rejects_invalid_key(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/admin/dashboard",
        headers={"X-Admin-Api-Key": "wrong-key"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_dashboard_metrics(client: AsyncClient) -> None:
    response = await client.get("/api/v1/admin/dashboard", headers=admin_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["total_tenants"] >= 1
    assert "subscription_breakdown" in body
    assert body["active_users"] >= 1


@pytest.mark.asyncio
async def test_admin_list_tenants(client: AsyncClient) -> None:
    response = await client.get("/api/v1/admin/tenants", headers=admin_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert any(item["company_id"] == str(DEMO_COMPANY_ID) for item in body["items"])


@pytest.mark.asyncio
async def test_admin_tenant_detail(client: AsyncClient) -> None:
    response = await client.get(
        f"/api/v1/admin/tenants/{DEMO_COMPANY_ID}",
        headers=admin_headers(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["company_id"] == str(DEMO_COMPANY_ID)
    assert body["is_active"] is True
    assert len(body["users"]) >= 1


@pytest.mark.asyncio
async def test_admin_suspend_and_activate_tenant(client: AsyncClient) -> None:
    suspend = await client.patch(
        f"/api/v1/admin/tenants/{DEMO_COMPANY_ID}/status",
        headers=admin_headers(),
        json={"is_active": False},
    )
    assert suspend.status_code == 200
    assert suspend.json()["is_active"] is False

    activate = await client.patch(
        f"/api/v1/admin/tenants/{DEMO_COMPANY_ID}/status",
        headers=admin_headers(),
        json={"is_active": True},
    )
    assert activate.status_code == 200
    assert activate.json()["is_active"] is True


@pytest.mark.asyncio
async def test_admin_list_users(client: AsyncClient) -> None:
    response = await client.get("/api/v1/admin/users", headers=admin_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 2


@pytest.mark.asyncio
async def test_admin_ai_usage(client: AsyncClient) -> None:
    response = await client.get("/api/v1/admin/ai-usage", headers=admin_headers())
    assert response.status_code == 200
    body = response.json()
    assert "tokens_this_month" in body
    assert "by_tenant" in body


@pytest.mark.asyncio
async def test_admin_system_health(client: AsyncClient) -> None:
    response = await client.get("/api/v1/admin/system-health", headers=admin_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["admin_api_key_configured"] is True
    assert "billing_mode" in body


@pytest.mark.asyncio
async def test_admin_audit_logs(client: AsyncClient) -> None:
    await client.patch(
        f"/api/v1/admin/tenants/{DEMO_COMPANY_ID}/status",
        headers=admin_headers(),
        json={"is_active": True},
    )
    response = await client.get("/api/v1/admin/audit-logs", headers=admin_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1


@pytest.mark.asyncio
async def test_admin_demo_reset_guard(client: AsyncClient, monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setattr("app.application.services.admin_service.settings.environment", "production")
    from app.core import config as config_mod

    config_mod.get_settings.cache_clear()
    response = await client.post("/api/v1/admin/demo/reset", headers=admin_headers())
    assert response.status_code == 403
    config_mod.get_settings.cache_clear()
