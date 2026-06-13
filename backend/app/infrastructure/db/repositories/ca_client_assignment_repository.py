"""SQLAlchemy implementation of CaClientAssignmentRepository."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import CaClientAssignmentRecord
from app.domain.enums import CaAssignmentStatus
from app.infrastructure.db.models.ca_client_assignment import CaClientAssignmentModel


class SqlAlchemyCaClientAssignmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: CaClientAssignmentRecord) -> CaClientAssignmentRecord:
        model = CaClientAssignmentModel(
            id=record.id,
            ca_user_id=record.ca_user_id,
            company_id=record.company_id,
            status=record.status,
            invited_by=record.invited_by,
            ca_firm_name=record.ca_firm_name,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_record(model)

    async def get_by_id(self, assignment_id: uuid.UUID) -> CaClientAssignmentRecord | None:
        stmt = select(CaClientAssignmentModel).where(CaClientAssignmentModel.id == assignment_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_record(model) if model else None

    async def get_by_ca_and_company(
        self, ca_user_id: uuid.UUID, company_id: uuid.UUID
    ) -> CaClientAssignmentRecord | None:
        stmt = select(CaClientAssignmentModel).where(
            CaClientAssignmentModel.ca_user_id == ca_user_id,
            CaClientAssignmentModel.company_id == company_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_record(model) if model else None

    async def list_for_ca(self, ca_user_id: uuid.UUID) -> list[CaClientAssignmentRecord]:
        stmt = (
            select(CaClientAssignmentModel)
            .where(CaClientAssignmentModel.ca_user_id == ca_user_id)
            .order_by(CaClientAssignmentModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_record(m) for m in result.scalars().all()]

    async def list_active_for_ca(self, ca_user_id: uuid.UUID) -> list[CaClientAssignmentRecord]:
        stmt = select(CaClientAssignmentModel).where(
            CaClientAssignmentModel.ca_user_id == ca_user_id,
            CaClientAssignmentModel.status == CaAssignmentStatus.ACTIVE,
        )
        result = await self._session.execute(stmt)
        return [self._to_record(m) for m in result.scalars().all()]

    async def list_for_company(self, company_id: uuid.UUID) -> list[CaClientAssignmentRecord]:
        stmt = (
            select(CaClientAssignmentModel)
            .where(
                CaClientAssignmentModel.company_id == company_id,
                CaClientAssignmentModel.status != CaAssignmentStatus.REVOKED,
            )
            .order_by(CaClientAssignmentModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_record(m) for m in result.scalars().all()]

    async def update(self, record: CaClientAssignmentRecord) -> CaClientAssignmentRecord:
        stmt = select(CaClientAssignmentModel).where(CaClientAssignmentModel.id == record.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.status = record.status
        model.ca_firm_name = record.ca_firm_name
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_record(model)

    @staticmethod
    def _to_record(model: CaClientAssignmentModel) -> CaClientAssignmentRecord:
        return CaClientAssignmentRecord(
            id=model.id,
            ca_user_id=model.ca_user_id,
            company_id=model.company_id,
            status=CaAssignmentStatus(model.status),
            invited_by=model.invited_by,
            ca_firm_name=model.ca_firm_name,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
