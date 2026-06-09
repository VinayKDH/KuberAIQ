"""Compliance obligations API integration tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_compliance_obligations_requires_profile(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.get("/api/v1/compliance/obligations", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["profile_complete"] is True
    assert data["summary"]["total_applicable"] > 0
    assert any(item["id"] == "gst_gstr1" for item in data["obligations"])


@pytest.mark.asyncio
async def test_compliance_calendar(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.get("/api/v1/compliance/calendar?days=60", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["profile_complete"] is True
    assert "events" in data


@pytest.mark.asyncio
async def test_complete_obligation(client: AsyncClient, auth_headers: dict) -> None:
    obligations = await client.get("/api/v1/compliance/obligations", headers=auth_headers)
    gst = next(item for item in obligations.json()["obligations"] if item["id"] == "gst_gstr1")
    resp = await client.post(
        f"/api/v1/compliance/obligations/gst_gstr1/complete",
        json={"period_key": gst["period_key"], "notes": "Filed on portal"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "COMPLETED"
    assert data["history"]


@pytest.mark.asyncio
async def test_update_compliance_profile(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.patch(
        "/api/v1/compliance/profile",
        json={"has_tds_applicable": True, "employee_count": 25},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_tds_applicable"] is True
    assert data["employee_count"] == 25

    obligations = await client.get("/api/v1/compliance/obligations", headers=auth_headers)
    ids = {item["id"] for item in obligations.json()["obligations"]}
    assert "it_tds_deposit" in ids
    assert "labour_pf" in ids


@pytest.mark.asyncio
async def test_dashboard_includes_compliance_alert(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.get(
        "/api/v1/dashboard",
        params={"from": "2026-04-01", "to": "2026-06-30"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert "compliance_alert" in resp.json()
