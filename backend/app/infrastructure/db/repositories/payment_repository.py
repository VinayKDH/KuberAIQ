"""SQLAlchemy implementation of PaymentRepository."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
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
