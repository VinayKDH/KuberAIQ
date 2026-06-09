"""Billing and payment-gated onboarding tests."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.constants import (
    DEMO_COMPANY_GSTIN,
    SUBSCRIPTION_PLAN_STARTER,
    SUBSCRIPTION_STARTER_AMOUNT_PAISE,
)
from app.core.security import create_access_token
from app.domain.enums import SubscriptionStatus, UserRole
from app.infrastructure.db.models.subscription import SubscriptionModel
from app.infrastructure.db.models.user import UserModel


@pytest.mark.asyncio
async def test_onboard_blocked_without_subscription(client: AsyncClient, db_engine) -> None:
    pending_user_id = uuid.uuid4()
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            UserModel(
                id=pending_user_id,
                company_id=None,
                email="pending@test.kuberaiq.com",
                full_name="Pending User",
                role=UserRole.OWNER,
            )
        )
        session.add(
            SubscriptionModel(
                user_id=pending_user_id,
                status=SubscriptionStatus.PENDING.value,
                plan_code=SUBSCRIPTION_PLAN_STARTER,
                amount_paise=SUBSCRIPTION_STARTER_AMOUNT_PAISE,
            )
        )
        await session.commit()

    headers = {
        "Authorization": f"Bearer {create_access_token(user_id=str(pending_user_id), company_id=None, role=UserRole.OWNER)}"
    }
    onboard = await client.post(
        "/api/v1/companies/onboard",
        headers=headers,
        json={
            "legal_name": "Test MSME Pvt Ltd",
            "gstin": "29ABCDE1234F1Z5",
            "address": "123 Test Street, Bengaluru",
            "invoice_prefix": "INV",
        },
    )
    assert onboard.status_code == 403


@pytest.mark.asyncio
async def test_onboard_rejects_duplicate_gstin(client: AsyncClient, db_engine) -> None:
    user_id = uuid.uuid4()
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        from datetime import datetime, timedelta, timezone

        session.add(
            UserModel(
                id=user_id,
                company_id=None,
                email="dup@test.kuberaiq.com",
                full_name="Dup User",
                role=UserRole.OWNER,
            )
        )
        now = datetime.now(timezone.utc)
        session.add(
            SubscriptionModel(
                user_id=user_id,
                status=SubscriptionStatus.ACTIVE.value,
                plan_code=SUBSCRIPTION_PLAN_STARTER,
                amount_paise=SUBSCRIPTION_STARTER_AMOUNT_PAISE,
                paid_at=now,
                current_period_end=now + timedelta(days=30),
            )
        )
        await session.commit()

    headers = {
        "Authorization": f"Bearer {create_access_token(user_id=str(user_id), company_id=None, role=UserRole.OWNER)}"
    }
    onboard = await client.post(
        "/api/v1/companies/onboard",
        headers=headers,
        json={
            "legal_name": "Another Business",
            "gstin": DEMO_COMPANY_GSTIN,
            "address": "123 Test Street, Bengaluru",
            "invoice_prefix": "INV",
        },
    )
    assert onboard.status_code == 409
    assert onboard.json()["error"]["code"] == "GSTIN_CONFLICT"


@pytest.mark.asyncio
async def test_mock_activate_issues_tokens(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    activate = await client.post("/api/v1/billing/mock-activate", headers=auth_headers)
    assert activate.status_code == 200
    body = activate.json()
    assert body["needs_payment"] is False


@pytest.mark.asyncio
async def test_demo_user_has_active_subscription(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    me = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert me.status_code == 200
    data = me.json()
    assert data["subscription_active"] is True
    assert data["needs_payment"] is False
