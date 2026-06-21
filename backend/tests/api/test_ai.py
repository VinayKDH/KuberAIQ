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
async def test_ai_chat_create_customer_name_then_labeled_phone(
    client: AsyncClient, auth_headers: dict
) -> None:
    first = await client.post(
        "/api/v1/ai/chat",
        json={"message": "create customer kamal joshi"},
        headers=auth_headers,
    )
    assert first.status_code == 200
    body = first.json()
    assert body["intent"] == "clarify"
    session_id = body["session_id"]

    second = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Name Kamal Joshi. Phone 9258843443", "session_id": session_id},
        headers=auth_headers,
    )
    assert second.status_code == 200
    follow = second.json()
    assert follow["requires_confirmation"] is True
    assert follow["pending_action"]["type"] == "create_customer"
    assert follow["pending_action"]["preview"]["name"] == "Kamal Joshi"
    assert follow["pending_action"]["preview"]["phone"] == "9258843443"


@pytest.mark.asyncio
async def test_ai_chat_phone_then_name_multiturn(client: AsyncClient, auth_headers: dict) -> None:
    first = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Add customer for 9000000000"},
        headers=auth_headers,
    )
    assert first.status_code == 200
    body = first.json()
    assert body["intent"] == "clarify"
    session_id = body["session_id"]

    second = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Raj Traders", "session_id": session_id},
        headers=auth_headers,
    )
    assert second.status_code == 200
    follow = second.json()
    assert follow["requires_confirmation"] is True
    assert follow["pending_action"]["type"] == "create_customer"
    assert follow["pending_action"]["preview"]["name"] == "Raj Traders"
    assert follow["pending_action"]["preview"]["phone"] == "9000000000"


@pytest.mark.asyncio
async def test_ai_chat_missing_customer_phone_multiturn(
    client: AsyncClient, auth_headers: dict
) -> None:
    chat = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Create the invoice for Unknown Co"},
        headers=auth_headers,
    )
    assert chat.status_code == 200
    body = chat.json()
    assert body["intent"] == "clarify"
    assert "Unknown Co" in body["message"]
    session_id = body["session_id"]

    phone = await client.post(
        "/api/v1/ai/chat",
        json={"message": "9111199999", "session_id": session_id},
        headers=auth_headers,
    )
    assert phone.status_code == 200
    follow = phone.json()
    assert follow["requires_confirmation"] is True
    assert follow["pending_action"]["type"] == "create_customer_and_invoice"
    assert follow["pending_action"]["preview"]["customer"]["name"] == "Unknown Co"
    assert follow["pending_action"]["preview"]["customer"]["phone"] == "9111199999"

    confirm = await client.post(
        "/api/v1/ai/confirm",
        json={
            "session_id": session_id,
            "pending_action": follow["pending_action"],
        },
        headers=auth_headers,
    )
    assert confirm.status_code == 200
    result = confirm.json()
    assert "invoice" in result["message"].lower()
    assert "created" in result["message"].lower()
    assert result["data"]["customer_name"] == "Unknown Co"
    assert result["data"]["invoice_number"]


@pytest.mark.asyncio
async def test_ai_chat_new_customer_with_phone_in_invoice_message(
    client: AsyncClient, auth_headers: dict
) -> None:
    chat = await client.post(
        "/api/v1/ai/chat",
        json={
            "message": "Create invoice for Brand New Co 9112233445 for 5 bags at 400",
        },
        headers=auth_headers,
    )
    assert chat.status_code == 200
    body = chat.json()
    assert body["requires_confirmation"] is True
    assert body["pending_action"]["type"] == "create_customer_and_invoice"
    assert body["pending_action"]["preview"]["customer"]["name"] == "Brand New Co"
    assert body["pending_action"]["preview"]["customer"]["phone"] == "9112233445"


@pytest.mark.asyncio
async def test_ai_chat_invoice_customer_name_with_inline_phone(
    client: AsyncClient, auth_headers: dict
) -> None:
    chat = await client.post(
        "/api/v1/ai/chat",
        json={
            "message": "Invoice New Person 9123456789 for 10 kg paneer at 200",
        },
        headers=auth_headers,
    )
    assert chat.status_code == 200
    body = chat.json()
    assert body["requires_confirmation"] is True
    assert body["pending_action"]["type"] == "create_customer_and_invoice"
    assert body["pending_action"]["preview"]["customer"]["name"] == "New Person"
    assert body["pending_action"]["preview"]["customer"]["phone"] == "9123456789"
    items = body["pending_action"]["preview"]["invoice"]["items"]
    assert items[0]["description"] == "Paneer"


@pytest.mark.asyncio
async def test_ai_chat_multi_item_invoice(client: AsyncClient, auth_headers: dict) -> None:
    cust = await client.post(
        "/api/v1/customers",
        json={"name": "AIMLGYAN", "phone": "9876501234"},
        headers=auth_headers,
    )
    assert cust.status_code == 201

    chat = await client.post(
        "/api/v1/ai/chat",
        json={
            "message": (
                "Create the invoice of 50 bags of cement and 2 litre of roof sealant "
                "for AIMLGYAN"
            ),
        },
        headers=auth_headers,
    )
    assert chat.status_code == 200
    body = chat.json()
    assert body["requires_confirmation"] is True
    assert "AIMLGYAN" in body["message"]
    assert "cement" in body["message"].lower()
    assert "sealant" in body["message"].lower()
    items = body["pending_action"]["preview"]["items"]
    assert len(items) == 2
    assert items[0]["hsn_sac"]
    assert float(items[0]["gst_rate"]) > 0


@pytest.mark.asyncio
async def test_ai_chat_add_customer_phone_only_clarifies(
    client: AsyncClient, auth_headers: dict
) -> None:
    chat = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Add customer for 9000000000"},
        headers=auth_headers,
    )
    assert chat.status_code == 200
    body = chat.json()
    assert body["intent"] == "clarify"
    assert "9000000000" in body["message"]
    assert body["requires_confirmation"] is False


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
