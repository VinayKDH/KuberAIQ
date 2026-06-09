"""SQLAlchemy implementation of InvoiceRepository."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.invoice import Invoice
from app.domain.enums import DocumentType, InvoiceStatus
from app.domain.services.invoice_numbering import format_invoice_number
from app.infrastructure.db.mappers.invoice_mapper import InvoiceMapper
from app.infrastructure.db.models.company import InvoiceCounterModel
from app.infrastructure.db.models.invoice import InvoiceModel


class SqlAlchemyInvoiceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, invoice: Invoice) -> Invoice:
        model = InvoiceMapper.to_model(invoice)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model, ["items"])
        return InvoiceMapper.to_domain(model)

    async def get_by_id(self, company_id: uuid.UUID, invoice_id: uuid.UUID) -> Invoice | None:
        stmt = (
            select(InvoiceModel)
            .options(selectinload(InvoiceModel.items))
            .where(
                InvoiceModel.company_id == company_id,
                InvoiceModel.id == invoice_id,
                InvoiceModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return InvoiceMapper.to_domain(model) if model else None

    async def get_by_number(
        self, company_id: uuid.UUID, invoice_number: str
    ) -> Invoice | None:
        stmt = (
            select(InvoiceModel)
            .options(selectinload(InvoiceModel.items))
            .where(
                InvoiceModel.company_id == company_id,
                InvoiceModel.invoice_number == invoice_number,
                InvoiceModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return InvoiceMapper.to_domain(model) if model else None

    async def update(self, invoice: Invoice) -> Invoice:
        stmt = (
            select(InvoiceModel)
            .options(selectinload(InvoiceModel.items))
            .where(
                InvoiceModel.id == invoice.id,
                InvoiceModel.company_id == invoice.company_id,
                InvoiceModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        InvoiceMapper.update_model(model, invoice)
        await self._session.flush()
        await self._session.refresh(model, ["items"])
        return InvoiceMapper.to_domain(model)

    async def search(
        self,
        company_id: uuid.UUID,
        *,
        q: str | None = None,
        status: InvoiceStatus | None = None,
        customer_id: uuid.UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        document_type: DocumentType | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Invoice], int]:
        base = (
            select(InvoiceModel)
            .options(selectinload(InvoiceModel.items))
            .where(
                InvoiceModel.company_id == company_id,
                InvoiceModel.deleted_at.is_(None),
            )
        )
        if document_type:
            base = base.where(InvoiceModel.document_type == document_type)
        else:
            base = base.where(InvoiceModel.document_type == DocumentType.INVOICE)
        if q:
            base = base.where(
                or_(
                    InvoiceModel.invoice_number.ilike(f"%{q}%"),
                )
            )
        if status:
            base = base.where(InvoiceModel.status == status)
        if customer_id:
            base = base.where(InvoiceModel.customer_id == customer_id)
        if from_date:
            base = base.where(InvoiceModel.issue_date >= from_date)
        if to_date:
            base = base.where(InvoiceModel.issue_date <= to_date)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = (
            base.order_by(InvoiceModel.issue_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        items = [InvoiceMapper.to_domain(m) for m in result.scalars().unique().all()]
        return items, total

    async def list_overdue(self, company_id: uuid.UUID) -> list[Invoice]:
        today = date.today()
        stmt = (
            select(InvoiceModel)
            .options(selectinload(InvoiceModel.items))
            .where(
                InvoiceModel.company_id == company_id,
                InvoiceModel.document_type == DocumentType.INVOICE,
                InvoiceModel.status.in_(
                    [InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE]
                ),
                InvoiceModel.due_date < today,
                InvoiceModel.amount_due > 0,
                InvoiceModel.deleted_at.is_(None),
            )
            .order_by(InvoiceModel.due_date)
        )
        result = await self._session.execute(stmt)
        return [InvoiceMapper.to_domain(m) for m in result.scalars().unique().all()]

    async def list_collectible(self, company_id: uuid.UUID) -> list[Invoice]:
        stmt = (
            select(InvoiceModel)
            .options(selectinload(InvoiceModel.items))
            .where(
                InvoiceModel.company_id == company_id,
                InvoiceModel.document_type == DocumentType.INVOICE,
                InvoiceModel.status.in_(
                    [InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.OVERDUE]
                ),
                InvoiceModel.amount_due > 0,
                InvoiceModel.deleted_at.is_(None),
            )
            .order_by(InvoiceModel.due_date)
        )
        result = await self._session.execute(stmt)
        return [InvoiceMapper.to_domain(m) for m in result.scalars().unique().all()]

    async def list_open_for_overdue_check(self, company_id: uuid.UUID, today: date) -> list[Invoice]:
        stmt = (
            select(InvoiceModel)
            .options(selectinload(InvoiceModel.items))
            .where(
                InvoiceModel.company_id == company_id,
                InvoiceModel.document_type == DocumentType.INVOICE,
                InvoiceModel.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID]),
                InvoiceModel.due_date < today,
                InvoiceModel.amount_due > 0,
                InvoiceModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return [InvoiceMapper.to_domain(m) for m in result.scalars().unique().all()]

    async def allocate_number(
        self, company_id: uuid.UUID, financial_year: str, prefix: str
    ) -> str:
        stmt = (
            select(InvoiceCounterModel)
            .where(
                InvoiceCounterModel.company_id == company_id,
                InvoiceCounterModel.financial_year == financial_year,
            )
            .with_for_update()
        )
        result = await self._session.execute(stmt)
        counter = result.scalar_one_or_none()
        if counter is None:
            counter = InvoiceCounterModel(
                company_id=company_id,
                financial_year=financial_year,
                last_value=0,
            )
            self._session.add(counter)
            await self._session.flush()
        counter.last_value += 1
        await self._session.flush()
        return format_invoice_number(prefix, financial_year, counter.last_value)

    async def list_issued_in_period(
        self, company_id: uuid.UUID, from_date: date, to_date: date
    ) -> list[Invoice]:
        issued_statuses = [
            InvoiceStatus.ISSUED,
            InvoiceStatus.PARTIALLY_PAID,
            InvoiceStatus.PAID,
            InvoiceStatus.OVERDUE,
        ]
        stmt = (
            select(InvoiceModel)
            .options(selectinload(InvoiceModel.items))
            .where(
                InvoiceModel.company_id == company_id,
                InvoiceModel.deleted_at.is_(None),
                InvoiceModel.issue_date >= from_date,
                InvoiceModel.issue_date <= to_date,
                InvoiceModel.status.in_(issued_statuses),
            )
            .order_by(InvoiceModel.issue_date)
        )
        result = await self._session.execute(stmt)
        return [InvoiceMapper.to_domain(m) for m in result.scalars().unique().all()]

    async def list_credit_notes_for_invoice(
        self, company_id: uuid.UUID, invoice_id: uuid.UUID
    ) -> list[Invoice]:
        stmt = (
            select(InvoiceModel)
            .options(selectinload(InvoiceModel.items))
            .where(
                InvoiceModel.company_id == company_id,
                InvoiceModel.original_invoice_id == invoice_id,
                InvoiceModel.document_type == DocumentType.CREDIT_NOTE,
                InvoiceModel.deleted_at.is_(None),
            )
            .order_by(InvoiceModel.issue_date.desc())
        )
        result = await self._session.execute(stmt)
        return [InvoiceMapper.to_domain(m) for m in result.scalars().unique().all()]
