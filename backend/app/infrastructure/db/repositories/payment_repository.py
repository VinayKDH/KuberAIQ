"""SQLAlchemy implementation of PaymentRepository."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import PaymentRecord
from app.domain.enums import PaymentMethod
from app.infrastructure.db.models.invoice import InvoiceModel
from app.infrastructure.db.models.payment import PaymentModel


class SqlAlchemyPaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, payment: PaymentRecord) -> PaymentRecord:
        model = PaymentModel(
            id=payment.id,
            company_id=payment.company_id,
            invoice_id=payment.invoice_id,
            amount=payment.amount,
            paid_on=payment.paid_on,
            method=payment.method,
            reference=payment.reference,
            note=payment.note,
            recorded_by=payment.recorded_by,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_record(model)

    async def get_by_id(
        self, company_id: uuid.UUID, payment_id: uuid.UUID
    ) -> PaymentRecord | None:
        stmt = select(PaymentModel).where(
            PaymentModel.id == payment_id,
            PaymentModel.company_id == company_id,
            PaymentModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_record(model) if model else None

    async def get_by_reference(
        self, company_id: uuid.UUID, reference: str
    ) -> PaymentRecord | None:
        stmt = select(PaymentModel).where(
            PaymentModel.company_id == company_id,
            PaymentModel.reference == reference,
            PaymentModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_record(model) if model else None

    async def list_by_invoice(self, invoice_id: uuid.UUID) -> list[PaymentRecord]:
        stmt = select(PaymentModel).where(
            PaymentModel.invoice_id == invoice_id,
            PaymentModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return [self._to_record(m) for m in result.scalars().all()]

    async def list_by_customer(
        self, company_id: uuid.UUID, customer_id: uuid.UUID
    ) -> list[PaymentRecord]:
        stmt = (
            select(PaymentModel)
            .join(InvoiceModel, PaymentModel.invoice_id == InvoiceModel.id)
            .where(
                PaymentModel.company_id == company_id,
                InvoiceModel.customer_id == customer_id,
                PaymentModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return [self._to_record(m) for m in result.scalars().all()]

    async def list_recent(
        self, company_id: uuid.UUID, *, limit: int, from_date: date | None = None
    ) -> list[PaymentRecord]:
        stmt = select(PaymentModel).where(
            PaymentModel.company_id == company_id,
            PaymentModel.deleted_at.is_(None),
        )
        if from_date is not None:
            stmt = stmt.where(PaymentModel.paid_on >= from_date)
        stmt = stmt.order_by(PaymentModel.paid_on.desc(), PaymentModel.created_at.desc()).limit(
            limit
        )
        result = await self._session.execute(stmt)
        return [self._to_record(m) for m in result.scalars().all()]

    async def sum_collected(
        self, company_id: uuid.UUID, from_date: date, to_date: date
    ) -> Decimal:
        stmt = select(func.coalesce(func.sum(PaymentModel.amount), 0)).where(
            PaymentModel.company_id == company_id,
            PaymentModel.deleted_at.is_(None),
            PaymentModel.paid_on >= from_date,
            PaymentModel.paid_on <= to_date,
        )
        result = await self._session.execute(stmt)
        return Decimal(str(result.scalar_one()))

    async def aggregate_by_method(
        self, company_id: uuid.UUID, from_date: date, to_date: date
    ) -> list[dict]:
        stmt = (
            select(PaymentModel.method, func.coalesce(func.sum(PaymentModel.amount), 0))
            .where(
                PaymentModel.company_id == company_id,
                PaymentModel.deleted_at.is_(None),
                PaymentModel.paid_on >= from_date,
                PaymentModel.paid_on <= to_date,
            )
            .group_by(PaymentModel.method)
        )
        result = await self._session.execute(stmt)
        return [
            {"method": str(row[0].value if hasattr(row[0], "value") else row[0]), "amount": float(row[1])}
            for row in result.all()
        ]

    async def soft_delete(self, payment_id: uuid.UUID) -> None:
        stmt = select(PaymentModel).where(PaymentModel.id == payment_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.deleted_at = datetime.now(timezone.utc)

    @staticmethod
    def _to_record(model: PaymentModel) -> PaymentRecord:
        return PaymentRecord(
            id=model.id,
            company_id=model.company_id,
            invoice_id=model.invoice_id,
            amount=model.amount,
            paid_on=model.paid_on,
            method=PaymentMethod(model.method),
            reference=model.reference,
            note=model.note,
            recorded_by=model.recorded_by,
        )
