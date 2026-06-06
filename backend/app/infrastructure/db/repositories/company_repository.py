"""SQLAlchemy implementation of CompanyRepository."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import CompanyRecord
from app.infrastructure.db.models.company import CompanyModel


class SqlAlchemyCompanyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, company_id: uuid.UUID) -> CompanyRecord | None:
        stmt = select(CompanyModel).where(
            CompanyModel.id == company_id,
            CompanyModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_record(model) if model else None

    async def get_state_code(self, company_id: uuid.UUID) -> str:
        stmt = select(CompanyModel.state_code).where(
            CompanyModel.id == company_id,
            CompanyModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def create(self, record: CompanyRecord) -> CompanyRecord:
        model = CompanyModel(
            id=record.id,
            legal_name=record.legal_name,
            gstin=record.gstin,
            state_code=record.state_code,
            invoice_prefix=record.invoice_prefix,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_record(model)

    @staticmethod
    def _to_record(model: CompanyModel) -> CompanyRecord:
        return CompanyRecord(
            id=model.id,
            legal_name=model.legal_name,
            gstin=model.gstin,
            state_code=model.state_code,
            invoice_prefix=model.invoice_prefix,
        )
