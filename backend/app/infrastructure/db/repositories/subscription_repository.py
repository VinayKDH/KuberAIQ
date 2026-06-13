"""Subscription repository."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import SubscriptionRecord
from app.domain.enums import SubscriptionStatus
from app.infrastructure.db.models.subscription import SubscriptionModel


class SqlAlchemySubscriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> SubscriptionRecord | None:
        stmt = select(SubscriptionModel).where(SubscriptionModel.user_id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_record(model) if model else None

    async def get_by_order_id(self, order_id: str) -> SubscriptionRecord | None:
        stmt = select(SubscriptionModel).where(SubscriptionModel.razorpay_order_id == order_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_record(model) if model else None

    async def list_active_past_period_end(self, as_of: datetime) -> list[SubscriptionRecord]:
        stmt = select(SubscriptionModel).where(
            SubscriptionModel.status == SubscriptionStatus.ACTIVE.value,
            SubscriptionModel.current_period_end.is_not(None),
            SubscriptionModel.current_period_end < as_of,
        )
        result = await self._session.execute(stmt)
        return [self._to_record(model) for model in result.scalars().all()]

    async def create(self, record: SubscriptionRecord) -> SubscriptionRecord:
        model = SubscriptionModel(
            id=record.id,
            user_id=record.user_id,
            status=record.status.value,
            plan_code=record.plan_code,
            amount_paise=record.amount_paise,
            razorpay_order_id=record.razorpay_order_id,
            razorpay_payment_id=record.razorpay_payment_id,
            paid_at=record.paid_at,
            current_period_end=record.current_period_end,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_record(model)

    async def update(self, record: SubscriptionRecord) -> SubscriptionRecord:
        stmt = select(SubscriptionModel).where(SubscriptionModel.id == record.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.status = record.status.value
        model.plan_code = record.plan_code
        model.amount_paise = record.amount_paise
        model.razorpay_order_id = record.razorpay_order_id
        model.razorpay_payment_id = record.razorpay_payment_id
        model.paid_at = record.paid_at
        model.current_period_end = record.current_period_end
        await self._session.flush()
        return self._to_record(model)

    @staticmethod
    def _to_record(model: SubscriptionModel) -> SubscriptionRecord:
        return SubscriptionRecord(
            id=model.id,
            user_id=model.user_id,
            status=SubscriptionStatus(model.status),
            plan_code=model.plan_code,
            amount_paise=model.amount_paise,
            razorpay_order_id=model.razorpay_order_id,
            razorpay_payment_id=model.razorpay_payment_id,
            paid_at=model.paid_at,
            current_period_end=model.current_period_end,
        )
