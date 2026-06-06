"""Payment use-case orchestration."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.application.ports.repositories import PaymentRecord
from app.core.constants import AuditAction, EntityType, ErrorCode
from app.core.errors import ConflictError, NotFoundError, ValidationAppError
from app.domain.enums import PaymentMethod
from app.domain.exceptions import PaymentExceedsDue
from app.domain.value_objects.money import Money


@dataclass
class RecordPaymentInput:
    amount: Decimal
    paid_on: date
    method: PaymentMethod
    reference: str | None = None
    note: str | None = None


class PaymentService:
    def __init__(self, uow_factory) -> None:
        self._uow_factory = uow_factory

    async def record(
        self,
        *,
        company_id: uuid.UUID,
        invoice_id: uuid.UUID,
        actor_id: uuid.UUID,
        data: RecordPaymentInput,
        ip: str | None = None,
    ) -> PaymentRecord:
        if data.amount <= 0:
            raise ValidationAppError("Payment amount must be positive")

        async with self._uow_factory() as uow:
            invoice = await uow.invoices.get_by_id(company_id, invoice_id)
            if not invoice:
                raise NotFoundError("Invoice not found")
            try:
                amount_due_before = invoice.amount_due.amount
                invoice.apply_payment(Money.of(data.amount))
            except PaymentExceedsDue as exc:
                raise ConflictError(str(exc), code=ErrorCode.PAYMENT_EXCEEDS_DUE) from exc

            payment = PaymentRecord(
                company_id=company_id,
                invoice_id=invoice_id,
                amount=data.amount,
                paid_on=data.paid_on,
                method=data.method,
                reference=data.reference,
                note=data.note,
                recorded_by=actor_id,
            )
            saved_payment = await uow.payments.create(payment)
            await uow.invoices.update(invoice)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.PAYMENT,
                entity_id=saved_payment.id,
                action=AuditAction.PAYMENT,
                before={"amount_due": str(amount_due_before)},
                after={
                    "amount": str(data.amount),
                    "invoice_status": invoice.status,
                    "amount_due": str(invoice.amount_due.amount),
                },
                ip_address=ip,
            )
            return saved_payment

    async def list_for_invoice(self, company_id: uuid.UUID, invoice_id: uuid.UUID) -> list[PaymentRecord]:
        async with self._uow_factory() as uow:
            invoice = await uow.invoices.get_by_id(company_id, invoice_id)
            if not invoice:
                raise NotFoundError("Invoice not found")
            return await uow.payments.list_by_invoice(invoice_id)
