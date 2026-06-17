"""WhatsApp inbound copilot tests."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.security import create_access_token
from app.domain.enums import SubscriptionStatus, UserRole
from app.infrastructure.db.models.company import CompanyModel
from app.infrastructure.db.models.subscription import SubscriptionModel
from app.infrastructure.db.models.user import UserModel
from app.infrastructure.notifications.phone_utils import normalize_whatsapp_phone


def test_normalize_whatsapp_phone_indian() -> None:
    assert normalize_whatsapp_phone("919876543210") == "9876543210"
    assert normalize_whatsapp_phone("+91 98765 43210") == "9876543210"


@pytest.mark.asyncio
async def test_update_whatsapp_phone_owner(client: AsyncClient, db_engine) -> None:
    company_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            CompanyModel(
                id=company_id,
                legal_name="WA Test Co",
                state_code="29",
            )
        )
        session.add(
            UserModel(
                id=owner_id,
                company_id=company_id,
                email="wa-owner@test.kuberaiq.com",
                full_name="WA Owner",
                role=UserRole.OWNER,
            )
        )
        session.add(
            SubscriptionModel(
                user_id=owner_id,
                status=SubscriptionStatus.ACTIVE.value,
                plan_code="starter_monthly",
                amount_paise=99900,
            )
        )
        await session.commit()

    headers = {
        "Authorization": f"Bearer {create_access_token(user_id=str(owner_id), company_id=str(company_id), role=UserRole.OWNER)}"
    }
    response = await client.patch(
        "/api/v1/auth/me/whatsapp-phone",
        headers=headers,
        json={"phone": "9876543210"},
    )
    assert response.status_code == 200
    assert response.json()["whatsapp_phone"] == "9876543210"


@pytest.mark.asyncio
async def test_whatsapp_inbound_routes_to_copilot(client: AsyncClient, db_engine) -> None:
    company_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            CompanyModel(
                id=company_id,
                legal_name="Inbound Co",
                state_code="29",
            )
        )
        session.add(
            UserModel(
                id=owner_id,
                company_id=company_id,
                email="inbound@test.kuberaiq.com",
                full_name="Inbound Owner",
                role=UserRole.OWNER,
                whatsapp_phone="9876501234",
            )
        )
        session.add(
            SubscriptionModel(
                user_id=owner_id,
                status=SubscriptionStatus.ACTIVE.value,
                plan_code="starter_monthly",
                amount_paise=99900,
            )
        )
        await session.commit()

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "919876501234",
                                    "type": "text",
                                    "text": {"body": "show dashboard"},
                                }
                            ],
                            "statuses": [],
                        }
                    }
                ]
            }
        ]
    }
    response = await client.post("/api/v1/webhooks/whatsapp", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "received"
    assert body["messages_handled"] == 1
