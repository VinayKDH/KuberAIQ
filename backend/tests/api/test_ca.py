"""CA persona API integration tests."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.core.constants import DEMO_CA_EMAIL
from app.core.security import create_access_token
from app.domain.enums import CaAssignmentStatus, UserRole
from app.infrastructure.db.models.user import UserModel
from app.startup.seed import DEMO_CA_USER_ID, DEMO_COMPANY_ID, DEMO_USER_ID


async def _create_ca_user(session, *, email: str = "advisor@ca.kuberaiq.com") -> uuid.UUID:
    ca_id = uuid.uuid4()
    session.add(
        UserModel(
            id=ca_id,
            company_id=None,
            email=email,
            full_name="Test CA",
            role=UserRole.CA,
        )
    )
    await session.commit()
    return ca_id


@pytest.mark.asyncio
async def test_ca_invite_accept_switch(client: AsyncClient, db_engine) -> None:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        ca_id = await _create_ca_user(session)

    owner_headers = {
        "Authorization": f"Bearer {create_access_token(user_id=str(DEMO_USER_ID), company_id=str(DEMO_COMPANY_ID), role=UserRole.OWNER)}"
    }

    invite = await client.post(
        "/api/v1/companies/me/advisors",
        headers=owner_headers,
        json={"email": "advisor@ca.kuberaiq.com", "ca_firm_name": "Test Firm"},
    )
    assert invite.status_code == 201
    assignment_id = invite.json()["id"]
    assert invite.json()["status"] == CaAssignmentStatus.PENDING.value

    ca_headers = {
        "Authorization": f"Bearer {create_access_token(user_id=str(ca_id), company_id=None, role=UserRole.CA)}"
    }

    clients_before = await client.get("/api/v1/ca/clients", headers=ca_headers)
    assert clients_before.status_code == 200
    assert any(c["id"] == assignment_id for c in clients_before.json()["items"])

    accept = await client.post(
        f"/api/v1/ca/invitations/{assignment_id}/accept",
        headers=ca_headers,
    )
    assert accept.status_code == 200
    accepted = next(c for c in accept.json()["items"] if c["id"] == assignment_id)
    assert accepted["status"] == CaAssignmentStatus.ACTIVE.value

    switch = await client.post(
        "/api/v1/ca/context",
        headers=ca_headers,
        json={"company_id": str(DEMO_COMPANY_ID)},
    )
    assert switch.status_code == 200
    body = switch.json()
    assert body["user"]["company_id"] == str(DEMO_COMPANY_ID)
    assert body["needs_payment"] is False
    assert body["needs_onboarding"] is False

    context_headers = {"Authorization": f"Bearer {body['access_token']}"}
    compliance = await client.get("/api/v1/compliance/dashboard", headers=context_headers)
    assert compliance.status_code == 200

    clear = await client.post("/api/v1/ca/context/clear", headers=context_headers)
    assert clear.status_code == 200
    assert clear.json()["user"]["company_id"] is None


@pytest.mark.asyncio
async def test_ca_cannot_create_invoice(client: AsyncClient) -> None:
    token = create_access_token(
        user_id=str(DEMO_CA_USER_ID), company_id=str(DEMO_COMPANY_ID), role=UserRole.CA
    )
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/api/v1/invoices",
        headers=headers,
        json={
            "customer_id": str(uuid.uuid4()),
            "issue_date": "2026-01-01",
            "due_date": "2026-01-15",
            "status": "DRAFT",
            "items": [
                {
                    "description": "Test item",
                    "quantity": 1,
                    "unit": "NOS",
                    "unit_price": 100,
                    "gst_rate": 18,
                }
            ],
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_demo_ca_mock_login(client: AsyncClient) -> None:
    login = await client.post("/api/v1/auth/mock-login", json={"email": DEMO_CA_EMAIL})
    assert login.status_code == 200
    body = login.json()
    assert body["user"]["role"] == UserRole.CA.value
    assert body["needs_payment"] is False
    assert body["needs_onboarding"] is False

    headers = {"Authorization": f"Bearer {body['access_token']}"}
    clients = await client.get("/api/v1/ca/clients", headers=headers)
    assert clients.status_code == 200


@pytest.mark.asyncio
async def test_owner_lists_advisors(client: AsyncClient) -> None:
    owner_headers = {
        "Authorization": f"Bearer {create_access_token(user_id=str(DEMO_USER_ID), company_id=str(DEMO_COMPANY_ID), role=UserRole.OWNER)}"
    }
    resp = await client.get("/api/v1/companies/me/advisors", headers=owner_headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 1
    assert any(i["ca_email"] == DEMO_CA_EMAIL for i in items)
