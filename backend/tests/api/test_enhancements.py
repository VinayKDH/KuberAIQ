"""Tests for Sprint 6 enhancements."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.constants import DEMO_USER_EMAIL


@pytest.mark.asyncio
async def test_me_reports_onboarding_complete(client: AsyncClient) -> None:
    login = await client.post("/api/v1/auth/mock-login", json={"email": DEMO_USER_EMAIL})
    token = login.json()["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["needs_onboarding"] is False


@pytest.mark.asyncio
async def test_audit_logs_list(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    resp = await client.get("/api/v1/audit-logs", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert body["total"] >= 0


@pytest.mark.asyncio
async def test_gst_report_csv(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    resp = await client.get(
        "/api/v1/invoices/reports/gst.csv",
        params={"from": "2025-04-01", "to": "2026-03-31"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "taxable_amount" in resp.text


@pytest.mark.asyncio
async def test_check_phone_not_found(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    resp = await client.get(
        "/api/v1/customers/check-phone",
        params={"phone": "9123456789"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["exists"] is False


@pytest.mark.asyncio
async def test_company_profile(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    resp = await client.get("/api/v1/companies/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["legal_name"]


@pytest.mark.asyncio
async def test_company_upi_and_reminder_settings(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    patch = await client.patch(
        "/api/v1/companies/me",
        json={
            "upi_id": "demo@upi",
            "upi_payee_name": "Demo Traders",
            "auto_reminders_enabled": False,
            "default_reminder_language": "hi",
        },
        headers=auth_headers,
    )
    assert patch.status_code == 200
    body = patch.json()
    assert body["upi_id"] == "demo@upi"
    assert body["auto_reminders_enabled"] is False
    assert body["default_reminder_language"] == "hi"


@pytest.mark.asyncio
async def test_company_msme_segment(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    patch = await client.patch(
        "/api/v1/companies/me",
        json={"msme_segment": "kirana"},
        headers=auth_headers,
    )
    assert patch.status_code == 200
    assert patch.json()["msme_segment"] == "kirana"

    invalid = await client.patch(
        "/api/v1/companies/me",
        json={"msme_segment": "invalid-segment"},
        headers=auth_headers,
    )
    assert invalid.status_code == 400
