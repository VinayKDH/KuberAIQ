"""Payment use-case orchestration."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
import csv
from io import StringIO

from app.application.ports.repositories import PaymentRecord
from app.core.config import settings
from app.core.constants import (
    AuditAction,
    EntityType,
    ErrorCode,
    PAYMENT_RECONCILIATION_AMOUNT_TOLERANCE,
    PAYMENT_SUMMARY_RECENT_LIMIT,
    RAZORPAY_INVOICE_REFERENCE_PREFIX,
    RAZORPAY_INVOICE_WEBHOOK_EVENTS,
    RAZORPAY_PAYMENT_REFERENCE_PREFIX,
    UPI_DEEP_LINK_STUB_NOTE,
)
from app.core.errors import ConflictError, NotFoundError, UnauthorizedError, ValidationAppError
from app.domain.enums import PaymentMethod
from app.domain.exceptions import PaymentExceedsDue
from app.domain.value_objects.money import Money
from app.infrastructure.billing.razorpay_client import RazorpayClient


@dataclass
class RecordPaymentInput:
    amount: Decimal
    paid_on: date
    method: PaymentMethod
    reference: str | None = None
    note: str | None = None


@dataclass
class CsvMatchApplyInput:
    invoice_id: uuid.UUID
    amount: Decimal
    paid_on: date | None = None
    method: PaymentMethod = PaymentMethod.BANK_TRANSFER
    reference: str | None = None


class PaymentService:
    def __init__(self, uow_factory) -> None:
        self._uow_factory = uow_factory

    async def record(
        self,
        *,
        company_id: uuid.UUID,
        invoice_id: uuid.UUID,
        actor_id: uuid.UUID | None,
        data: RecordPaymentInput,
        ip: str | None = None,
        commit: bool = True,
    ) -> PaymentRecord:
        if data.amount <= 0:
            raise ValidationAppError("Payment amount must be positive")

        async with self._uow_factory() as uow:
            invoice = await uow.invoices.get_by_id(company_id, invoice_id)
            if not invoice:
                raise NotFoundError("Invoice not found")
            if data.reference:
                existing = await uow.payments.get_by_reference(company_id, data.reference)
                if existing:
                    return existing
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
            if commit:
                await uow.commit()
            return saved_payment

    async def reverse(
        self,
        *,
        company_id: uuid.UUID,
        invoice_id: uuid.UUID,
        payment_id: uuid.UUID,
        actor_id: uuid.UUID,
        ip: str | None = None,
    ) -> PaymentRecord:
        async with self._uow_factory() as uow:
            invoice = await uow.invoices.get_by_id(company_id, invoice_id)
            if not invoice:
                raise NotFoundError("Invoice not found")
            payment = await uow.payments.get_by_id(company_id, payment_id)
            if not payment or payment.invoice_id != invoice_id:
                raise NotFoundError("Payment not found")

            amount_due_before = invoice.amount_due.amount
            status_before = invoice.status
            invoice.reverse_payment(Money.of(payment.amount), today=date.today())
            await uow.payments.soft_delete(payment.id)
            await uow.invoices.update(invoice)
            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.PAYMENT,
                entity_id=payment.id,
                action=AuditAction.PAYMENT_REVERSE,
                before={
                    "amount": str(payment.amount),
                    "amount_due": str(amount_due_before),
                    "invoice_status": str(status_before),
                },
                after={
                    "amount_due": str(invoice.amount_due.amount),
                    "invoice_status": str(invoice.status),
                },
                ip_address=ip,
            )
            return payment

    async def list_for_invoice(self, company_id: uuid.UUID, invoice_id: uuid.UUID) -> list[PaymentRecord]:
        async with self._uow_factory() as uow:
            invoice = await uow.invoices.get_by_id(company_id, invoice_id)
            if not invoice:
                raise NotFoundError("Invoice not found")
            return await uow.payments.list_by_invoice(invoice_id)

    async def suggest_matches_from_csv(self, company_id: uuid.UUID, csv_text: str) -> list[dict]:
        rows = list(csv.DictReader(StringIO(csv_text)))
        suggestions: list[dict] = []
        async with self._uow_factory() as uow:
            invoices = await uow.invoices.list_collectible(company_id)
            by_number = {inv.invoice_number: inv for inv in invoices if inv.invoice_number}

        tolerance = Decimal(str(PAYMENT_RECONCILIATION_AMOUNT_TOLERANCE))
        for row in rows:
            reference = (row.get("reference") or row.get("invoice_number") or "").strip()
            amount = Decimal(str(row.get("amount") or "0"))
            paid_on_raw = (row.get("paid_on") or row.get("date") or "").strip()
            paid_on = date.fromisoformat(paid_on_raw) if paid_on_raw else date.today()
            match = by_number.get(reference)
            if not match:
                for inv in invoices:
                    if abs(inv.amount_due.amount - amount) <= tolerance:
                        match = inv
                        break
            suggestions.append(
                {
                    "reference": reference,
                    "amount": float(amount),
                    "paid_on": paid_on.isoformat(),
                    "matched_invoice_id": str(match.id) if match else None,
                    "matched_invoice_number": match.invoice_number if match else None,
                    "match_confidence": "exact" if match and reference else ("amount" if match else "none"),
                }
            )
        return suggestions

    async def apply_csv_matches(
        self,
        *,
        company_id: uuid.UUID,
        actor_id: uuid.UUID,
        matches: list[CsvMatchApplyInput],
        ip: str | None = None,
    ) -> list[PaymentRecord]:
        applied: list[PaymentRecord] = []
        for match in matches:
            payment = await self.record(
                company_id=company_id,
                invoice_id=match.invoice_id,
                actor_id=actor_id,
                data=RecordPaymentInput(
                    amount=match.amount,
                    paid_on=match.paid_on or date.today(),
                    method=match.method,
                    reference=match.reference,
                    note="Bank CSV reconciliation",
                ),
                ip=ip,
            )
            applied.append(payment)
        return applied

    async def collection_summary(self, company_id: uuid.UUID) -> dict:
        today = date.today()
        async with self._uow_factory() as uow:
            collected_today = await uow.payments.sum_collected(company_id, today, today)
            recent = await uow.payments.list_recent(
                company_id, limit=PAYMENT_SUMMARY_RECENT_LIMIT, from_date=today - timedelta(days=30)
            )
            invoice_numbers: dict[uuid.UUID, str | None] = {}
            recent_rows: list[dict] = []
            for payment in recent:
                if payment.invoice_id not in invoice_numbers:
                    inv = await uow.invoices.get_by_id(company_id, payment.invoice_id)
                    invoice_numbers[payment.invoice_id] = inv.invoice_number if inv else None
                recent_rows.append(
                    {
                        "id": str(payment.id),
                        "invoice_id": str(payment.invoice_id),
                        "invoice_number": invoice_numbers.get(payment.invoice_id),
                        "amount": float(payment.amount),
                        "paid_on": payment.paid_on.isoformat(),
                        "method": payment.method.value,
                    }
                )
        return {
            "collected_today": float(collected_today),
            "recent_payments": recent_rows,
        }

    async def payment_analytics(self, company_id: uuid.UUID) -> dict:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        async with self._uow_factory() as uow:
            collected_week = await uow.payments.sum_collected(company_id, week_start, today)
            collected_month = await uow.payments.sum_collected(company_id, month_start, today)
            by_method = await uow.payments.aggregate_by_method(company_id, month_start, today)
        return {
            "collected_week": float(collected_week),
            "collected_month": float(collected_month),
            "method_breakdown": by_method,
        }

    async def handle_razorpay_invoice_webhook(self, body: bytes, signature: str) -> bool:
        if not self._verify_webhook(body, signature):
            raise UnauthorizedError("Invalid webhook signature")

        payload = json.loads(body)
        event = payload.get("event")
        if event not in RAZORPAY_INVOICE_WEBHOOK_EVENTS:
            return False

        reference_id, payment_id, amount_paise = self._extract_invoice_payment(payload, event)
        if not reference_id or not reference_id.startswith(RAZORPAY_INVOICE_REFERENCE_PREFIX):
            return False
        if not payment_id:
            return False

        try:
            invoice_id = uuid.UUID(reference_id[len(RAZORPAY_INVOICE_REFERENCE_PREFIX) :])
        except ValueError:
            return False

        amount = Decimal(amount_paise) / Decimal("100")
        payment_ref = f"{RAZORPAY_PAYMENT_REFERENCE_PREFIX}{payment_id}"

        async with self._uow_factory() as uow:
            invoice = await uow.invoices.get_by_id_only(invoice_id)
            if not invoice:
                return False
            existing = await uow.payments.get_by_reference(invoice.company_id, payment_ref)
            if existing:
                return True
            company_id = invoice.company_id

        await self.record(
            company_id=company_id,
            invoice_id=invoice_id,
            actor_id=None,
            data=RecordPaymentInput(
                amount=amount,
                paid_on=date.today(),
                method=PaymentMethod.CARD,
                reference=payment_ref,
                note="Razorpay payment link webhook",
            ),
        )
        return True

    async def record_upi_stub(
        self,
        *,
        company_id: uuid.UUID,
        invoice_id: uuid.UUID,
        actor_id: uuid.UUID,
        amount: Decimal | None = None,
        ip: str | None = None,
    ) -> dict:
        async with self._uow_factory() as uow:
            invoice = await uow.invoices.get_by_id(company_id, invoice_id)
            if not invoice:
                raise NotFoundError("Invoice not found")
            pay_amount = amount or invoice.amount_due.amount
        return {
            "invoice_id": str(invoice_id),
            "amount": float(pay_amount),
            "note": UPI_DEEP_LINK_STUB_NOTE,
            "prompt_record": True,
        }

    @staticmethod
    def _verify_webhook(body: bytes, signature: str) -> bool:
        if settings.use_mock_billing and not settings.razorpay_webhook_secret:
            return True
        client = RazorpayClient()
        return client.verify_webhook_signature(body, signature)

    @staticmethod
    def _extract_invoice_payment(payload: dict, event: str) -> tuple[str | None, str | None, int]:
        if event == "payment_link.paid":
            pl = payload.get("payload", {}).get("payment_link", {}).get("entity", {})
            payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
            return (
                pl.get("reference_id"),
                payment.get("id"),
                int(payment.get("amount") or pl.get("amount") or 0),
            )
        payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
        notes = payment.get("notes") or {}
        reference_id = notes.get("reference_id") or payment.get("description") or ""
        return reference_id, payment.get("id"), int(payment.get("amount") or 0)
