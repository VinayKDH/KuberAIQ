"""Admin routes protected by ADMIN_API_KEY."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select

from app.core.config import settings
from app.core.errors import ForbiddenError
from app.infrastructure.db.models.company import CompanyModel
from app.infrastructure.db.models.subscription import SubscriptionModel
from app.infrastructure.db.models.user import UserModel
from app.infrastructure.db.session import AsyncSessionLocal

router = APIRouter(prefix="/admin", tags=["admin"])


async def require_admin_key(x_admin_api_key: Annotated[str | None, Header()] = None) -> None:
    if not settings.admin_api_key or x_admin_api_key != settings.admin_api_key:
        raise ForbiddenError("Invalid admin API key")


@router.get("/tenants")
async def list_tenants(_: Annotated[None, Depends(require_admin_key)]) -> dict:
    async with AsyncSessionLocal() as session:
        rows = (
            await session.execute(
                select(CompanyModel, UserModel, SubscriptionModel)
                .join(UserModel, UserModel.company_id == CompanyModel.id)
                .join(SubscriptionModel, SubscriptionModel.user_id == UserModel.id, isouter=True)
                .where(UserModel.role == "OWNER", CompanyModel.deleted_at.is_(None))
            )
        ).all()
    items = []
    for company, owner, subscription in rows:
        items.append(
            {
                "company_id": str(company.id),
                "company_name": company.legal_name,
                "owner_email": owner.email,
                "subscription_status": subscription.status if subscription else "NONE",
                "plan_code": subscription.plan_code if subscription else None,
            }
        )
    return {"items": items, "total": len(items)}
