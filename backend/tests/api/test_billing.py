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
async def test_new_user_subscribe_onboard_flow(client: AsyncClient) -> None:
    from app.domain.value_objects.gstin import _checksum

    email = f"e2e+{uuid.uuid4().hex[:8]}@test.kuberaiq.com"
    login = await client.post("/api/v1/auth/mock-login", json={"email": email})
    assert login.status_code == 200
    login_body = login.json()
    assert login_body["needs_payment"] is True

    headers = {"Authorization": f"Bearer {login_body['access_token']}"}
    activate = await client.post("/api/v1/billing/mock-activate", headers=headers)
    assert activate.status_code == 200
    tokens = activate.json()
    assert tokens["needs_onboarding"] is True

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    suffix = f"{uuid.uuid4().int % 10000:04d}"
    first14 = f"29AAAAA{suffix}A1Z"
    gstin = first14 + _checksum(first14)

    onboard = await client.post(
        "/api/v1/companies/onboard",
        headers=headers,
        json={
            "legal_name": "E2E Flow Traders",
            "gstin": gstin,
            "address": "42 Test Lane, Bengaluru",
            "invoice_prefix": "INV",
        },
    )
    assert onboard.status_code == 200
    onboard_body = onboard.json()
    assert onboard_body["needs_onboarding"] is False

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {onboard_body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["user"]["company_id"] is not None
    assert me.json()["needs_onboarding"] is False


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


@pytest.mark.asyncio
async def test_billing_status_marks_expired_past_period(client: AsyncClient, db_engine) -> None:
    from datetime import datetime, timedelta, timezone

    user_id = uuid.uuid4()
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    past_end = datetime.now(timezone.utc) - timedelta(days=1)
    async with session_factory() as session:
        session.add(
            UserModel(
                id=user_id,
                company_id=None,
                email="expired@test.kuberaiq.com",
                full_name="Expired User",
                role=UserRole.OWNER,
            )
        )
        session.add(
            SubscriptionModel(
                user_id=user_id,
                status=SubscriptionStatus.ACTIVE.value,
                plan_code=SUBSCRIPTION_PLAN_STARTER,
                amount_paise=SUBSCRIPTION_STARTER_AMOUNT_PAISE,
                paid_at=past_end - timedelta(days=30),
                current_period_end=past_end,
            )
        )
        await session.commit()

    headers = {
        "Authorization": f"Bearer {create_access_token(user_id=str(user_id), company_id=None, role=UserRole.OWNER)}"
    }
    status = await client.get("/api/v1/billing/status", headers=headers)
    assert status.status_code == 200
    body = status.json()
    assert body["subscription_status"] == SubscriptionStatus.EXPIRED.value
    assert body["subscription_active"] is False
    assert body["needs_payment"] is True
    assert body["plan_name"] == "KuberAIQ Starter"


@pytest.mark.asyncio
async def test_expire_subscriptions_past_period_job(client: AsyncClient, db_engine) -> None:
    from datetime import datetime, timedelta, timezone

    from app.workers.jobs import expire_subscriptions_past_period

    user_id = uuid.uuid4()
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    past_end = datetime.now(timezone.utc) - timedelta(hours=2)
    async with session_factory() as session:
        session.add(
            UserModel(
                id=user_id,
                company_id=None,
                email="job-expired@test.kuberaiq.com",
                full_name="Job Expired User",
                role=UserRole.OWNER,
            )
        )
        session.add(
            SubscriptionModel(
                user_id=user_id,
                status=SubscriptionStatus.ACTIVE.value,
                plan_code=SUBSCRIPTION_PLAN_STARTER,
                amount_paise=SUBSCRIPTION_STARTER_AMOUNT_PAISE,
                paid_at=past_end - timedelta(days=30),
                current_period_end=past_end,
            )
        )
        await session.commit()

    expired_count = await expire_subscriptions_past_period()
    assert expired_count == 1

    headers = {
        "Authorization": f"Bearer {create_access_token(user_id=str(user_id), company_id=None, role=UserRole.OWNER)}"
    }
    status = await client.get("/api/v1/billing/status", headers=headers)
    assert status.json()["subscription_status"] == SubscriptionStatus.EXPIRED.value
