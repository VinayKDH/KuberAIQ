"""SQLAlchemy implementation of compliance status repository."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import ComplianceStatusRecord
from app.infrastructure.db.models.compliance import CompanyComplianceStatusModel, ComplianceObligationModel
from app.infrastructure.db.seeds.compliance_catalog import compliance_catalog_rows


class SqlAlchemyComplianceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ensure_catalog_seeded(self) -> None:
        stmt = select(ComplianceObligationModel.id).limit(1)
        result = await self._session.execute(stmt)
        if result.scalar_one_or_none():
            return
        for row in compliance_catalog_rows():
            self._session.add(ComplianceObligationModel(**row))
        await self._session.flush()

    async def get_status(
        self,
        company_id: uuid.UUID,
        obligation_id: str,
        period_key: str,
    ) -> ComplianceStatusRecord | None:
        stmt = select(CompanyComplianceStatusModel).where(
            CompanyComplianceStatusModel.company_id == company_id,
            CompanyComplianceStatusModel.obligation_id == obligation_id,
            CompanyComplianceStatusModel.period_key == period_key,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_record(model) if model else None

    async def list_for_company(self, company_id: uuid.UUID) -> list[ComplianceStatusRecord]:
        stmt = (
            select(CompanyComplianceStatusModel)
            .where(CompanyComplianceStatusModel.company_id == company_id)
            .order_by(CompanyComplianceStatusModel.due_date.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_record(row) for row in result.scalars().all()]

    async def upsert_status(self, record: ComplianceStatusRecord) -> ComplianceStatusRecord:
        stmt = select(CompanyComplianceStatusModel).where(
            CompanyComplianceStatusModel.company_id == record.company_id,
            CompanyComplianceStatusModel.obligation_id == record.obligation_id,
            CompanyComplianceStatusModel.period_key == record.period_key,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            model = CompanyComplianceStatusModel(
                id=record.id,
                company_id=record.company_id,
                obligation_id=record.obligation_id,
                period_key=record.period_key,
                status=record.status,
                due_date=record.due_date,
                completed_at=record.completed_at,
                completed_by=record.completed_by,
                notes=record.notes,
            )
            self._session.add(model)
        else:
            model.status = record.status
            model.due_date = record.due_date
            model.completed_at = record.completed_at
            model.completed_by = record.completed_by
            model.notes = record.notes
        await self._session.flush()
        return self._to_record(model)

    async def list_completion_history(
        self,
        company_id: uuid.UUID,
        obligation_id: str,
        *,
        limit: int = 12,
    ) -> list[ComplianceStatusRecord]:
        stmt = (
            select(CompanyComplianceStatusModel)
            .where(
                CompanyComplianceStatusModel.company_id == company_id,
                CompanyComplianceStatusModel.obligation_id == obligation_id,
                CompanyComplianceStatusModel.completed_at.is_not(None),
            )
            .order_by(CompanyComplianceStatusModel.completed_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_record(row) for row in result.scalars().all()]

    @staticmethod
    def _to_record(model: CompanyComplianceStatusModel) -> ComplianceStatusRecord:
        return ComplianceStatusRecord(
            id=model.id,
            company_id=model.company_id,
            obligation_id=model.obligation_id,
            period_key=model.period_key,
            status=model.status,
            due_date=model.due_date,
            completed_at=model.completed_at,
            completed_by=model.completed_by,
            notes=model.notes,
        )
