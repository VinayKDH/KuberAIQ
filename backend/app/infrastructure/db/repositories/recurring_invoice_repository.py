"""Recurring invoice template repository."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import RecurringInvoiceTemplateRecord
from app.infrastructure.db.models.recurring_invoice import RecurringInvoiceTemplateModel


class SqlAlchemyRecurringInvoiceTemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: RecurringInvoiceTemplateRecord) -> RecurringInvoiceTemplateRecord:
        model = RecurringInvoiceTemplateModel(
            id=record.id,
            company_id=record.company_id,
            customer_id=record.customer_id,
            name=record.name,
            items_json=record.items_json,
            frequency=record.frequency,
            next_run_date=record.next_run_date,
            last_run_at=record.last_run_at,
            is_active=record.is_active,
            created_by=record.created_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_record(model)

    async def list_for_company(self, company_id: uuid.UUID) -> list[RecurringInvoiceTemplateRecord]:
        stmt = (
            select(RecurringInvoiceTemplateModel)
            .where(RecurringInvoiceTemplateModel.company_id == company_id)
            .order_by(RecurringInvoiceTemplateModel.next_run_date)
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [self._to_record(model) for model in models]

    async def get_by_id(
        self, company_id: uuid.UUID, template_id: uuid.UUID
    ) -> RecurringInvoiceTemplateRecord | None:
        model = (
            await self._session.execute(
                select(RecurringInvoiceTemplateModel).where(
                    RecurringInvoiceTemplateModel.id == template_id,
                    RecurringInvoiceTemplateModel.company_id == company_id,
                )
            )
        ).scalar_one_or_none()
        return self._to_record(model) if model else None

    async def list_due_templates(self, as_of) -> list[RecurringInvoiceTemplateRecord]:
        stmt = select(RecurringInvoiceTemplateModel).where(
            RecurringInvoiceTemplateModel.is_active.is_(True),
            RecurringInvoiceTemplateModel.next_run_date <= as_of,
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [self._to_record(model) for model in models]

    async def update(self, record: RecurringInvoiceTemplateRecord) -> RecurringInvoiceTemplateRecord:
        model = (
            await self._session.execute(
                select(RecurringInvoiceTemplateModel).where(
                    RecurringInvoiceTemplateModel.id == record.id
                )
            )
        ).scalar_one()
        model.name = record.name
        model.items_json = record.items_json
        model.frequency = record.frequency
        model.next_run_date = record.next_run_date
        model.last_run_at = record.last_run_at
        model.is_active = record.is_active
        await self._session.flush()
        return self._to_record(model)

    @staticmethod
    def _to_record(model: RecurringInvoiceTemplateModel) -> RecurringInvoiceTemplateRecord:
        return RecurringInvoiceTemplateRecord(
            id=model.id,
            company_id=model.company_id,
            customer_id=model.customer_id,
            name=model.name,
            items_json=model.items_json,
            frequency=model.frequency,
            next_run_date=model.next_run_date,
            last_run_at=model.last_run_at,
            is_active=model.is_active,
            created_by=model.created_by,
        )
