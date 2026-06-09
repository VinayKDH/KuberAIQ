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

    async def get_by_gstin(self, gstin: str) -> CompanyRecord | None:
        stmt = select(CompanyModel).where(
            CompanyModel.gstin == gstin.strip().upper(),
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

    async def list_active_ids(self) -> list[uuid.UUID]:
        stmt = select(CompanyModel.id).where(CompanyModel.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, record: CompanyRecord) -> CompanyRecord:
        model = CompanyModel(
            id=record.id,
            legal_name=record.legal_name,
            gstin=record.gstin,
            state_code=record.state_code,
            address=record.address,
            invoice_prefix=record.invoice_prefix,
            upi_id=record.upi_id,
            upi_payee_name=record.upi_payee_name,
            auto_reminders_enabled=record.auto_reminders_enabled,
            default_reminder_language=record.default_reminder_language,
            entity_type=record.entity_type,
            turnover_band=record.turnover_band,
            gstr1_filing_frequency=record.gstr1_filing_frequency,
            employee_count=record.employee_count,
            udyam_number=record.udyam_number,
            has_tds_applicable=record.has_tds_applicable,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_record(model)

    async def update(self, record: CompanyRecord) -> CompanyRecord:
        stmt = select(CompanyModel).where(
            CompanyModel.id == record.id,
            CompanyModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.legal_name = record.legal_name
        model.gstin = record.gstin
        model.state_code = record.state_code
        model.address = record.address
        model.invoice_prefix = record.invoice_prefix
        model.upi_id = record.upi_id
        model.upi_payee_name = record.upi_payee_name
        model.auto_reminders_enabled = record.auto_reminders_enabled
        model.default_reminder_language = record.default_reminder_language
        model.entity_type = record.entity_type
        model.turnover_band = record.turnover_band
        model.gstr1_filing_frequency = record.gstr1_filing_frequency
        model.employee_count = record.employee_count
        model.udyam_number = record.udyam_number
        model.has_tds_applicable = record.has_tds_applicable
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
            address=model.address,
            upi_id=model.upi_id,
            upi_payee_name=model.upi_payee_name,
            auto_reminders_enabled=model.auto_reminders_enabled,
            default_reminder_language=model.default_reminder_language,
            entity_type=model.entity_type,
            turnover_band=model.turnover_band,
            gstr1_filing_frequency=model.gstr1_filing_frequency,
            employee_count=model.employee_count,
            udyam_number=model.udyam_number,
            has_tds_applicable=model.has_tds_applicable,
        )
