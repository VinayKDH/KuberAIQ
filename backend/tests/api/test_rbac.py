"""RBAC enforcement tests — staff forbidden actions."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.domain.enums import UserRole
from app.infrastructure.db.models.user import UserModel
from app.startup.seed import DEMO_COMPANY_ID


@pytest.mark.asyncio
async def test_staff_cannot_patch_company(client: AsyncClient, db_engine) -> None:
    staff_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.run_sync(lambda sync: _insert_staff(sync, staff_id))
    headers = {
        "Authorization": f"Bearer {create_access_token(user_id=str(staff_id), company_id=str(DEMO_COMPANY_ID), role=UserRole.STAFF)}"
    }
    response = await client.patch(
        "/api/v1/companies/me",
        headers=headers,
        json={"legal_name": "Hacked Name"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_staff_cannot_cancel_invoice(
    client: AsyncClient, db_engine, auth_headers: dict[str, str]
) -> None:
    staff_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.run_sync(lambda sync: _insert_staff(sync, staff_id))
    staff_headers = {
        "Authorization": f"Bearer {create_access_token(user_id=str(staff_id), company_id=str(DEMO_COMPANY_ID), role=UserRole.STAFF)}"
    }
    invoices = await client.get("/api/v1/invoices", headers=auth_headers)
    assert invoices.status_code == 200
    items = invoices.json()["items"]
    if not items:
        pytest.skip("No invoices in seed data")
    invoice_id = items[0]["id"]
    response = await client.post(
        f"/api/v1/invoices/{invoice_id}:cancel",
        headers=staff_headers,
        json={"reason": "test"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_staff_cannot_checkout_billing(client: AsyncClient, db_engine) -> None:
    staff_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.run_sync(lambda sync: _insert_staff(sync, staff_id))
    headers = {
        "Authorization": f"Bearer {create_access_token(user_id=str(staff_id), company_id=str(DEMO_COMPANY_ID), role=UserRole.STAFF)}"
    }
    response = await client.post("/api/v1/billing/checkout", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_owner_can_patch_company(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.patch(
        "/api/v1/companies/me",
        headers=auth_headers,
        json={"upi_id": "demo@upi"},
    )
    assert response.status_code == 200


def _insert_staff(sync, staff_id: uuid.UUID) -> None:
    from sqlalchemy.orm import Session

    session = Session(bind=sync)
    session.add(
        UserModel(
            id=staff_id,
            company_id=DEMO_COMPANY_ID,
            email=f"staff-{staff_id.hex[:8]}@demo.kuberaiq.com",
            full_name="Demo Staff",
            role=UserRole.STAFF,
        )
    )
    session.commit()
