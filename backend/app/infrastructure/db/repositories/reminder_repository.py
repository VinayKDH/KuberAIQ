"""SQLAlchemy implementation of ReminderRepository."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import ReminderRecord
from app.domain.enums import ReminderChannel, ReminderStatus
from app.infrastructure.db.models.reminder import ReminderModel


class SqlAlchemyReminderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, reminder: ReminderRecord) -> ReminderRecord:
        model = ReminderModel(
            id=reminder.id,
            company_id=reminder.company_id,
            invoice_id=reminder.invoice_id,
            customer_id=reminder.customer_id,
            channel=reminder.channel,
            status=reminder.status,
            message=reminder.message,
            trigger=reminder.trigger,
            sent_by=reminder.sent_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_record(model)

    async def update_status(
        self,
        reminder_id: uuid.UUID,
        *,
        status: ReminderStatus,
        provider_message_id: str | None = None,
        error: str | None = None,
    ) -> ReminderRecord:
        stmt = select(ReminderModel).where(ReminderModel.id == reminder_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.status = status
        model.provider_message_id = provider_message_id
        model.error = error
        if status == ReminderStatus.SENT:
            model.sent_at = datetime.now(timezone.utc)
        await self._session.flush()
        return self._to_record(model)

    async def list_by_invoice(self, invoice_id: uuid.UUID) -> list[ReminderRecord]:
        stmt = (
            select(ReminderModel)
            .where(ReminderModel.invoice_id == invoice_id)
            .order_by(ReminderModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_record(m) for m in result.scalars().all()]

    async def last_sent_for_invoice(self, invoice_id: uuid.UUID) -> ReminderRecord | None:
        stmt = (
            select(ReminderModel)
            .where(
                ReminderModel.invoice_id == invoice_id,
                ReminderModel.status == ReminderStatus.SENT,
            )
            .order_by(ReminderModel.sent_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_record(model) if model else None

    async def has_sent_trigger(self, invoice_id: uuid.UUID, trigger: str) -> bool:
        stmt = (
            select(ReminderModel.id)
            .where(
                ReminderModel.invoice_id == invoice_id,
                ReminderModel.trigger == trigger,
                ReminderModel.status == ReminderStatus.SENT,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _to_record(model: ReminderModel) -> ReminderRecord:
        record = ReminderRecord(
            id=model.id,
            company_id=model.company_id,
            invoice_id=model.invoice_id,
            customer_id=model.customer_id,
            channel=ReminderChannel(model.channel),
            message=model.message,
            sent_by=model.sent_by,
            trigger=model.trigger,
        )
        record.status = ReminderStatus(model.status)
        record.provider_message_id = model.provider_message_id
        record.error = model.error
        record.sent_at = model.sent_at
        record.trigger = model.trigger
        return record
