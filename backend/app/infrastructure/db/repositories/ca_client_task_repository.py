"""SQLAlchemy implementation of CaClientTaskRepository."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import CaClientTaskRecord
from app.infrastructure.db.models.ca_client_task import CaClientTaskModel


class SqlAlchemyCaClientTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: CaClientTaskRecord) -> CaClientTaskRecord:
        model = CaClientTaskModel(
            id=record.id,
            assignment_id=record.assignment_id,
            company_id=record.company_id,
            ca_user_id=record.ca_user_id,
            title=record.title,
            description=record.description,
            due_date=record.due_date,
            status=record.status,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_record(model)

    async def get_by_id(self, task_id: uuid.UUID) -> CaClientTaskRecord | None:
        stmt = select(CaClientTaskModel).where(CaClientTaskModel.id == task_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_record(model) if model else None

    async def list_for_company(
        self, company_id: uuid.UUID, *, ca_user_id: uuid.UUID | None = None
    ) -> list[CaClientTaskRecord]:
        stmt = select(CaClientTaskModel).where(CaClientTaskModel.company_id == company_id)
        if ca_user_id:
            stmt = stmt.where(CaClientTaskModel.ca_user_id == ca_user_id)
        stmt = stmt.order_by(CaClientTaskModel.due_date.nulls_last(), CaClientTaskModel.created_at.desc())
        result = await self._session.execute(stmt)
        return [self._to_record(m) for m in result.scalars().all()]

    async def update(self, record: CaClientTaskRecord) -> CaClientTaskRecord:
        stmt = select(CaClientTaskModel).where(CaClientTaskModel.id == record.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.title = record.title
        model.description = record.description
        model.due_date = record.due_date
        model.status = record.status
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_record(model)

    async def delete(self, task_id: uuid.UUID) -> None:
        stmt = select(CaClientTaskModel).where(CaClientTaskModel.id == task_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        await self._session.delete(model)

    @staticmethod
    def _to_record(model: CaClientTaskModel) -> CaClientTaskRecord:
        return CaClientTaskRecord(
            id=model.id,
            assignment_id=model.assignment_id,
            company_id=model.company_id,
            ca_user_id=model.ca_user_id,
            title=model.title,
            description=model.description,
            due_date=model.due_date,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
