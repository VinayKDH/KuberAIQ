"""Live billing enforcement on tenant API routes."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.domain.enums import SubscriptionStatus, UserRole
from app.infrastructure.db.models.company import CompanyModel
from app.infrastructure.db.models.subscription import SubscriptionModel
from app.infrastructure.db.models.user import UserModel


@pytest.mark.asyncio
async def test_expired_subscription_blocks_tenant_routes(
    client: AsyncClient, db_engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core import config as config_mod

    monkeypatch.setattr(config_mod.settings, "use_mock_billing", False)
    user_id = uuid.uuid4()
    company_id = uuid.uuid4()

    async with db_engine.begin() as conn:
        await conn.run_sync(
            lambda sync: _seed_expired_owner(sync, user_id=user_id, company_id=company_id)
        )

    headers = {
        "Authorization": f"Bearer {create_access_token(user_id=str(user_id), company_id=str(company_id), role=UserRole.OWNER)}"
    }
    dashboard = await client.get("/api/v1/dashboard?from=2026-04-01&to=2026-06-30", headers=headers)
    assert dashboard.status_code == 403

    billing = await client.get("/api/v1/billing/status", headers=headers)
    assert billing.status_code == 200


def _seed_expired_owner(sync, *, user_id: uuid.UUID, company_id: uuid.UUID) -> None:
    from datetime import datetime, timezone

    from sqlalchemy.orm import Session

    session = Session(bind=sync)
    session.add(
        CompanyModel(
            id=company_id,
            legal_name="Expired Co",
            gstin="29AAAAA0000A1Z5",
            state_code="29",
            address="Test",
        )
    )
    session.add(
        UserModel(
            id=user_id,
            company_id=company_id,
            email="expired@kuberaiq.com",
            full_name="Expired Owner",
            role=UserRole.OWNER,
        )
    )
    session.add(
        SubscriptionModel(
            id=uuid.uuid4(),
            user_id=user_id,
            status=SubscriptionStatus.EXPIRED,
            plan_code="starter_monthly",
            amount_paise=99900,
            current_period_end=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
    )
    session.commit()
