"""SQLAlchemy implementation of QuotationRepository."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.quotation import Quotation
from app.domain.enums import QuotationStatus
from app.domain.services.invoice_numbering import format_invoice_number
from app.infrastructure.db.mappers.quotation_mapper import QuotationMapper
from app.infrastructure.db.models.company import InvoiceCounterModel
from app.infrastructure.db.models.quotation import QuotationModel


class SqlAlchemyQuotationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, quotation: Quotation) -> Quotation:
        model = QuotationMapper.to_model(quotation)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model, ["items"])
        return QuotationMapper.to_domain(model)

    async def get_by_id(self, company_id: uuid.UUID, quotation_id: uuid.UUID) -> Quotation | None:
        stmt = (
            select(QuotationModel)
            .options(selectinload(QuotationModel.items))
            .where(
                QuotationModel.company_id == company_id,
                QuotationModel.id == quotation_id,
                QuotationModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return QuotationMapper.to_domain(model) if model else None

    async def update(self, quotation: Quotation) -> Quotation:
        stmt = (
            select(QuotationModel)
            .options(selectinload(QuotationModel.items))
            .where(
                QuotationModel.id == quotation.id,
                QuotationModel.company_id == quotation.company_id,
                QuotationModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        QuotationMapper.update_model(model, quotation)
        await self._session.flush()
        await self._session.refresh(model, ["items"])
        return QuotationMapper.to_domain(model)

    async def search(
        self,
        company_id: uuid.UUID,
        *,
        q: str | None = None,
        status: QuotationStatus | None = None,
        customer_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Quotation], int]:
        base = (
            select(QuotationModel)
            .options(selectinload(QuotationModel.items))
            .where(
                QuotationModel.company_id == company_id,
                QuotationModel.deleted_at.is_(None),
            )
        )
        if q:
            base = base.where(QuotationModel.quotation_number.ilike(f"%{q}%"))
        if status:
            base = base.where(QuotationModel.status == status)
        if customer_id:
            base = base.where(QuotationModel.customer_id == customer_id)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = (
            base.order_by(QuotationModel.issue_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        items = [QuotationMapper.to_domain(m) for m in result.scalars().unique().all()]
        return items, total

    async def list_expired_candidates(self, company_id: uuid.UUID, today: date) -> list[Quotation]:
        stmt = (
            select(QuotationModel)
            .options(selectinload(QuotationModel.items))
            .where(
                QuotationModel.company_id == company_id,
                QuotationModel.valid_until < today,
                QuotationModel.status.in_(
                    [QuotationStatus.DRAFT, QuotationStatus.SENT, QuotationStatus.ACCEPTED]
                ),
                QuotationModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return [QuotationMapper.to_domain(m) for m in result.scalars().unique().all()]

    async def allocate_number(
        self, company_id: uuid.UUID, financial_year: str, prefix: str
    ) -> str:
        counter_key = f"QT:{financial_year}"
        stmt = (
            select(InvoiceCounterModel)
            .where(
                InvoiceCounterModel.company_id == company_id,
                InvoiceCounterModel.financial_year == counter_key,
            )
            .with_for_update()
        )
        result = await self._session.execute(stmt)
        counter = result.scalar_one_or_none()
        if counter is None:
            counter = InvoiceCounterModel(
                company_id=company_id,
                financial_year=counter_key,
                last_value=0,
            )
            self._session.add(counter)
            await self._session.flush()
        counter.last_value += 1
        await self._session.flush()
        return format_invoice_number(prefix, financial_year, counter.last_value)
