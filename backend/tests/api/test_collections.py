"""Collections API integration tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_collections_overdue_and_dashboard(client: AsyncClient, auth_headers: dict) -> None:
    cust = await client.post(
        "/api/v1/customers",
        json={"name": "Overdue Co", "phone": "9988776655"},
        headers=auth_headers,
    )
    customer_id = cust.json()["id"]
    await client.post(
        "/api/v1/invoices",
        json={
            "customer_id": customer_id,
            "issue_date": "2026-01-01",
            "due_date": "2026-01-15",
            "status": "ISSUED",
            "items": [{"description": "Steel", "quantity": 1, "unit_price": 5000, "gst_rate": 18}],
        },
        headers=auth_headers,
    )

    overdue = await client.get("/api/v1/collections/overdue", headers=auth_headers)
    assert overdue.status_code == 200
    assert "items" in overdue.json()

    summary = await client.get("/api/v1/collections/dashboard", headers=auth_headers)
    assert summary.status_code == 200
    body = summary.json()
    assert "overdue_count" in body
    assert "total_outstanding" in body
    assert "invoices" in body

    preview = await client.post("/api/v1/collections/reminders/bulk:preview", headers=auth_headers)
    assert preview.status_code == 200
    assert "count" in preview.json()

    dash = await client.get("/api/v1/collections/dashboard", headers=auth_headers)
    assert dash.status_code == 200
    dash_body = dash.json()
    assert "total_overdue" in dash_body
    assert "reminded_today" in dash_body


@pytest.mark.asyncio
async def test_send_reminder_for_overdue_invoice(client: AsyncClient, auth_headers: dict) -> None:
    phone = f"9{__import__('random').randint(100000000, 999999999)}"
    cust = await client.post(
        "/api/v1/customers",
        json={"name": "Reminder Co", "phone": phone},
        headers=auth_headers,
    )
    customer_id = cust.json()["id"]
    inv = await client.post(
        "/api/v1/invoices",
        json={
            "customer_id": customer_id,
            "issue_date": "2026-01-01",
            "due_date": "2026-01-10",
            "status": "ISSUED",
            "items": [{"description": "Goods", "quantity": 1, "unit_price": 1000, "gst_rate": 18}],
        },
        headers=auth_headers,
    )
    invoice_id = inv.json()["id"]
    reminder = await client.post(
        "/api/v1/collections/reminders",
        json={"invoice_id": invoice_id},
        headers=auth_headers,
    )
    assert reminder.status_code == 200
    assert reminder.json()["status"] in {"SENT", "PENDING"}


@pytest.mark.asyncio
async def test_reminder_preview(client: AsyncClient, auth_headers: dict) -> None:
    phone = f"9{__import__('random').randint(100000000, 999999999)}"
    cust = await client.post(
        "/api/v1/customers",
        json={"name": "Preview Co", "phone": phone},
        headers=auth_headers,
    )
    customer_id = cust.json()["id"]
    inv = await client.post(
        "/api/v1/invoices",
        json={
            "customer_id": customer_id,
            "issue_date": "2026-01-01",
            "due_date": "2026-01-10",
            "status": "ISSUED",
            "items": [{"description": "Goods", "quantity": 1, "unit_price": 1000, "gst_rate": 18}],
        },
        headers=auth_headers,
    )
    invoice_id = inv.json()["id"]
    preview = await client.get(
        f"/api/v1/collections/reminders/preview?invoice_id={invoice_id}",
        headers=auth_headers,
    )
    assert preview.status_code == 200
    body = preview.json()
    assert body["invoice_id"] == invoice_id
    assert "Preview Co" in body["message"]
    assert body["amount_due"]


@pytest.mark.asyncio
async def test_collections_call_today(client: AsyncClient, auth_headers: dict) -> None:
    phone = f"9{__import__('random').randint(100000000, 999999999)}"
    cust = await client.post(
        "/api/v1/customers",
        json={"name": "Call Today Co", "phone": phone},
        headers=auth_headers,
    )
    customer_id = cust.json()["id"]
    inv = await client.post(
        "/api/v1/invoices",
        json={
            "customer_id": customer_id,
            "issue_date": "2026-06-01",
            "due_date": "2026-06-06",
            "status": "ISSUED",
            "items": [{"description": "Goods", "quantity": 1, "unit_price": 2500, "gst_rate": 18}],
        },
        headers=auth_headers,
    )
    invoice_id = inv.json()["id"]

    resp = await client.get("/api/v1/collections/call-today", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert any(item["invoice_id"] == invoice_id for item in body)
    match = next(item for item in body if item["invoice_id"] == invoice_id)
    assert match["customer_name"] == "Call Today Co"
    assert match["priority_score"] > 0
