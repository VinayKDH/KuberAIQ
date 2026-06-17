"""Expense repository."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import ExpenseRecord
from app.infrastructure.db.models.expense import ExpenseModel


class SqlAlchemyExpenseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: ExpenseRecord) -> ExpenseRecord:
        model = ExpenseModel(
            id=record.id,
            company_id=record.company_id,
            expense_date=record.expense_date,
            category=record.category,
            amount=record.amount,
            vendor_name=record.vendor_name,
            note=record.note,
            created_by=record.created_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_record(model)

    async def list_for_company(self, company_id: uuid.UUID, page: int, page_size: int) -> tuple[list[ExpenseRecord], int]:
        base = select(ExpenseModel).where(
            ExpenseModel.company_id == company_id,
            ExpenseModel.deleted_at.is_(None),
        )
        total = (
            await self._session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        models = (
            await self._session.execute(
                base.order_by(ExpenseModel.expense_date.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()
        return [self._to_record(model) for model in models], total

    async def get_by_id(self, company_id: uuid.UUID, expense_id: uuid.UUID) -> ExpenseRecord | None:
        model = (
            await self._session.execute(
                select(ExpenseModel).where(
                    ExpenseModel.company_id == company_id,
                    ExpenseModel.id == expense_id,
                    ExpenseModel.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        return self._to_record(model) if model else None

    async def update(self, record: ExpenseRecord) -> ExpenseRecord:
        model = (
            await self._session.execute(
                select(ExpenseModel).where(ExpenseModel.id == record.id)
            )
        ).scalar_one()
        model.expense_date = record.expense_date
        model.category = record.category
        model.amount = record.amount
        model.vendor_name = record.vendor_name
        model.note = record.note
        await self._session.flush()
        return self._to_record(model)

    async def soft_delete(self, company_id: uuid.UUID, expense_id: uuid.UUID) -> None:
        model = (
            await self._session.execute(
                select(ExpenseModel).where(
                    ExpenseModel.company_id == company_id,
                    ExpenseModel.id == expense_id,
                    ExpenseModel.deleted_at.is_(None),
                )
            )
        ).scalar_one()
        model.deleted_at = datetime.now(timezone.utc)
        await self._session.flush()

    @staticmethod
    def _to_record(model: ExpenseModel) -> ExpenseRecord:
        return ExpenseRecord(
            id=model.id,
            company_id=model.company_id,
            expense_date=model.expense_date,
            category=model.category,
            amount=model.amount,
            vendor_name=model.vendor_name,
            note=model.note,
            created_by=model.created_by,
        )
