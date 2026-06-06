"""Seed demo company and user for local development."""
from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select

from app.core.constants import (
    DEFAULT_INVOICE_PREFIX,
    DEMO_COMPANY_ADDRESS,
    DEMO_COMPANY_GSTIN,
    DEMO_COMPANY_NAME,
    DEMO_COMPANY_STATE,
    DEMO_USER_EMAIL,
    DEMO_USER_NAME,
)
from app.domain.enums import UserRole
from app.infrastructure.db.models.company import CompanyModel
from app.infrastructure.db.models.user import UserModel
from app.infrastructure.db.session import AsyncSessionLocal

logger = structlog.get_logger(__name__)

DEMO_COMPANY_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
DEMO_USER_ID = uuid.UUID("00000000-0000-4000-8000-000000000002")


async def seed_demo_data() -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            select(CompanyModel).where(CompanyModel.id == DEMO_COMPANY_ID)
        )
        if existing.scalar_one_or_none():
            logger.info("demo_seed_skipped", reason="already_exists")
            return

        company = CompanyModel(
            id=DEMO_COMPANY_ID,
            legal_name=DEMO_COMPANY_NAME,
            gstin=DEMO_COMPANY_GSTIN,
            state_code=DEMO_COMPANY_STATE,
            address=DEMO_COMPANY_ADDRESS,
            invoice_prefix=DEFAULT_INVOICE_PREFIX,
        )
        user = UserModel(
            id=DEMO_USER_ID,
            company_id=DEMO_COMPANY_ID,
            email=DEMO_USER_EMAIL,
            full_name=DEMO_USER_NAME,
            role=UserRole.OWNER,
        )
        session.add(company)
        session.add(user)
        await session.commit()
        logger.info("demo_seed_complete", company_id=str(DEMO_COMPANY_ID), email=DEMO_USER_EMAIL)
