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
    body = resp.json()
    assert body["intent"] in {"list_unpaid", "list_overdue"}
    assert "pending" in body["message"].lower() or "unpaid" in body["message"].lower()


@pytest.mark.asyncio
async def test_ai_chat_gst_clarify_has_suggestions(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.post(
        "/api/v1/ai/chat",
        json={"message": "When is my GSTR-1 due?"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["intent"] == "clarify"
    assert "compliance" in body["message"].lower()
    assert body["suggested_actions"]


@pytest.mark.asyncio
async def test_ai_chat_help(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.post(
        "/api/v1/ai/chat",
        json={"message": "help"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["suggested_actions"]


@pytest.mark.asyncio
async def test_ai_chat_confirm_with_client_pending_action(
    client: AsyncClient, auth_headers: dict
) -> None:
    cust = await client.post(
        "/api/v1/customers",
        json={"name": "AI Confirm Co", "phone": "9111122233"},
        headers=auth_headers,
    )
    assert cust.status_code == 201

    chat = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Invoice AI Confirm Co for 5 bags at 400"},
        headers=auth_headers,
    )
    assert chat.status_code == 200
    body = chat.json()
    assert body["requires_confirmation"] is True

    confirm = await client.post(
        "/api/v1/ai/chat",
        json={
            "message": "yes",
            "session_id": "new-worker-session",
            "pending_action": body["pending_action"],
        },
        headers=auth_headers,
    )
    assert confirm.status_code == 200
    assert confirm.json()["requires_confirmation"] is False
    assert "invoice" in confirm.json()["message"].lower()


@pytest.mark.asyncio
async def test_ai_confirm_create_customer(client: AsyncClient, auth_headers: dict) -> None:
    chat = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Add customer Sprint Four Co 9123456780"},
        headers=auth_headers,
    )
    assert chat.status_code == 200
    body = chat.json()
    assert body["requires_confirmation"] is True
    assert body["pending_action"]["type"] == "create_customer"

    confirm = await client.post(
        "/api/v1/ai/confirm",
        json={
            "session_id": body["session_id"],
            "pending_action": body["pending_action"],
        },
        headers=auth_headers,
    )
    assert confirm.status_code == 200
    assert "created" in confirm.json()["message"].lower()


@pytest.mark.asyncio
async def test_ai_chat_yes_confirms_pending_invoice(client: AsyncClient, auth_headers: dict) -> None:
    cust = await client.post(
        "/api/v1/customers",
        json={"name": "AI Invoice Co", "phone": "9112233445"},
        headers=auth_headers,
    )
    assert cust.status_code == 201

    chat = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Invoice AI Invoice Co for 10 bags at 350"},
        headers=auth_headers,
    )
    assert chat.status_code == 200
    body = chat.json()
    assert body["requires_confirmation"] is True
    session_id = body["session_id"]

    yes = await client.post(
        "/api/v1/ai/chat",
        json={"message": "yes", "session_id": session_id},
        headers=auth_headers,
    )
    assert yes.status_code == 200
    assert yes.json()["requires_confirmation"] is False
    assert "invoice" in yes.json()["message"].lower()


@pytest.mark.asyncio
async def test_ai_bulk_reminder_confirm(client: AsyncClient, auth_headers: dict) -> None:
    chat = await client.post(
        "/api/v1/ai/chat",
        json={"message": "send reminders to all overdue"},
        headers=auth_headers,
    )
    assert chat.status_code == 200
    body = chat.json()
    if body.get("requires_confirmation"):
        confirm = await client.post(
            "/api/v1/ai/confirm",
            json={
                "session_id": body["session_id"],
                "pending_action": body["pending_action"],
            },
            headers=auth_headers,
        )
        assert confirm.status_code == 200
        assert confirm.json()["requires_confirmation"] is False
