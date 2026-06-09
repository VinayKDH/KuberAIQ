"""Seed demo company and user for local development."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select

from app.core.constants import (
    DEFAULT_INVOICE_PREFIX,
    DEMO_COMPANY_ADDRESS,
    DEMO_COMPANY_AUTO_REMINDERS,
    DEMO_COMPANY_EMPLOYEE_COUNT,
    DEMO_COMPANY_ENTITY_TYPE,
    DEMO_COMPANY_GSTIN,
    DEMO_COMPANY_GSTR1_FREQUENCY,
    DEMO_COMPANY_HAS_TDS,
    DEMO_COMPANY_NAME,
    DEMO_COMPANY_REMINDER_LANGUAGE,
    DEMO_COMPANY_STATE,
    DEMO_COMPANY_TURNOVER_BAND,
    DEMO_COMPANY_UDYAM_NUMBER,
    DEMO_COMPANY_UPI_ID,
    DEMO_COMPANY_UPI_PAYEE_NAME,
    DEMO_USER_EMAIL,
    DEMO_USER_NAME,
    LEGACY_DEMO_USER_EMAIL,
)
from app.domain.enums import UserRole
from app.core.config import settings
from app.core.constants import SUBSCRIPTION_PLAN_STARTER
from app.domain.enums import SubscriptionStatus
from app.infrastructure.db.models.company import CompanyModel
from app.infrastructure.db.models.subscription import SubscriptionModel
from app.infrastructure.db.models.user import UserModel
from app.infrastructure.db.session import AsyncSessionLocal

logger = structlog.get_logger(__name__)

DEMO_COMPANY_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
DEMO_USER_ID = uuid.UUID("00000000-0000-4000-8000-000000000002")


def _apply_demo_company_defaults(company: CompanyModel) -> bool:
    """Apply demo UPI + compliance defaults when missing. Returns True if mutated."""
    changed = False
    defaults: list[tuple[str, object]] = [
        ("upi_id", DEMO_COMPANY_UPI_ID),
        ("upi_payee_name", DEMO_COMPANY_UPI_PAYEE_NAME),
        ("auto_reminders_enabled", DEMO_COMPANY_AUTO_REMINDERS),
        ("default_reminder_language", DEMO_COMPANY_REMINDER_LANGUAGE),
        ("entity_type", DEMO_COMPANY_ENTITY_TYPE),
        ("turnover_band", DEMO_COMPANY_TURNOVER_BAND),
        ("gstr1_filing_frequency", DEMO_COMPANY_GSTR1_FREQUENCY),
        ("employee_count", DEMO_COMPANY_EMPLOYEE_COUNT),
        ("udyam_number", DEMO_COMPANY_UDYAM_NUMBER),
        ("has_tds_applicable", DEMO_COMPANY_HAS_TDS),
    ]
    for field, value in defaults:
        if getattr(company, field) in (None, "") and value is not None:
            setattr(company, field, value)
            changed = True
    return changed


async def seed_demo_data() -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            select(CompanyModel).where(CompanyModel.id == DEMO_COMPANY_ID)
        )
        company = existing.scalar_one_or_none()
        if company:
            company_changed = _apply_demo_company_defaults(company)
            user_changed = False
            user_result = await session.execute(
                select(UserModel).where(UserModel.id == DEMO_USER_ID)
            )
            user = user_result.scalar_one_or_none()
            if user and user.email == LEGACY_DEMO_USER_EMAIL:
                user.email = DEMO_USER_EMAIL
                user_changed = True
            sub_result = await session.execute(
                select(SubscriptionModel).where(SubscriptionModel.user_id == DEMO_USER_ID)
            )
            sub = sub_result.scalar_one_or_none()
            sub_changed = False
            if not sub:
                now = datetime.now(timezone.utc)
                session.add(
                    SubscriptionModel(
                        id=uuid.uuid4(),
                        user_id=DEMO_USER_ID,
                        status=SubscriptionStatus.ACTIVE.value,
                        plan_code=SUBSCRIPTION_PLAN_STARTER,
                        amount_paise=settings.subscription_plan_amount_paise,
                        paid_at=now,
                        current_period_end=now + timedelta(days=30),
                    )
                )
                sub_changed = True
            if company_changed or user_changed or sub_changed:
                await session.commit()
                logger.info("demo_seed_backfill", company_id=str(DEMO_COMPANY_ID))
            else:
                logger.info("demo_seed_skipped", reason="already_exists")
            return

        company = CompanyModel(
            id=DEMO_COMPANY_ID,
            legal_name=DEMO_COMPANY_NAME,
            gstin=DEMO_COMPANY_GSTIN,
            state_code=DEMO_COMPANY_STATE,
            address=DEMO_COMPANY_ADDRESS,
            invoice_prefix=DEFAULT_INVOICE_PREFIX,
            upi_id=DEMO_COMPANY_UPI_ID,
            upi_payee_name=DEMO_COMPANY_UPI_PAYEE_NAME,
            auto_reminders_enabled=DEMO_COMPANY_AUTO_REMINDERS,
            default_reminder_language=DEMO_COMPANY_REMINDER_LANGUAGE,
            entity_type=DEMO_COMPANY_ENTITY_TYPE,
            turnover_band=DEMO_COMPANY_TURNOVER_BAND,
            gstr1_filing_frequency=DEMO_COMPANY_GSTR1_FREQUENCY,
            employee_count=DEMO_COMPANY_EMPLOYEE_COUNT,
            udyam_number=DEMO_COMPANY_UDYAM_NUMBER,
            has_tds_applicable=DEMO_COMPANY_HAS_TDS,
        )
        user = UserModel(
            id=DEMO_USER_ID,
            company_id=DEMO_COMPANY_ID,
            email=DEMO_USER_EMAIL,
            full_name=DEMO_USER_NAME,
            role=UserRole.OWNER,
        )
        now = datetime.now(timezone.utc)
        session.add(company)
        session.add(user)
        session.add(
            SubscriptionModel(
                id=uuid.uuid4(),
                user_id=DEMO_USER_ID,
                status=SubscriptionStatus.ACTIVE.value,
                plan_code=SUBSCRIPTION_PLAN_STARTER,
                amount_paise=settings.subscription_plan_amount_paise,
                paid_at=now,
                current_period_end=now + timedelta(days=30),
            )
        )
        await session.commit()
        logger.info("demo_seed_complete", company_id=str(DEMO_COMPANY_ID), email=DEMO_USER_EMAIL)
