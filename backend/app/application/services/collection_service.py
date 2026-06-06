"""Collections use-case orchestration."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from app.application.ports.notifier import NotifierPort
from app.application.ports.repositories import ReminderRecord
from app.core.constants import REMINDER_COOLDOWN_HOURS, AuditAction, EntityType, ErrorCode
from app.core.errors import ConflictError, NotFoundError
from app.domain.enums import InvoiceStatus, ReminderChannel, ReminderStatus


@dataclass
class SendReminderInput:
    invoice_id: uuid.UUID
    channel: ReminderChannel = ReminderChannel.WHATSAPP
    language: str = "en"


class CollectionService:
    def __init__(self, uow_factory, notifier: NotifierPort) -> None:
        self._uow_factory = uow_factory
        self._notifier = notifier

    async def mark_overdue(self, company_id: uuid.UUID) -> int:
        today = date.today()
        count = 0
        async with self._uow_factory() as uow:
            invoices = await uow.invoices.list_open_for_overdue_check(company_id, today)
            for invoice in invoices:
                if invoice.mark_overdue_if_due(today):
                    await uow.invoices.update(invoice)
                    count += 1
        return count

    async def list_overdue(self, company_id: uuid.UUID) -> list[dict]:
        async with self._uow_factory() as uow:
            invoices = await uow.invoices.list_overdue(company_id)
            today = date.today()
            results = []
            for inv in invoices:
                customer = await uow.customers.get_by_id(company_id, inv.customer_id)
                last = await uow.reminders.last_sent_for_invoice(inv.id)
                results.append(
                    {
                        "invoice": inv,
                        "customer_name": customer.name if customer else "Unknown",
                        "days_overdue": (today - inv.due_date).days,
                        "last_reminder": last,
                    }
                )
            results.sort(key=lambda r: (-r["invoice"].amount_due.amount, -r["days_overdue"]))
            return results

    async def send_reminder(
        self,
        *,
        company_id: uuid.UUID,
        actor_id: uuid.UUID,
        data: SendReminderInput,
        ip: str | None = None,
    ) -> ReminderRecord:
        async with self._uow_factory() as uow:
            invoice = await uow.invoices.get_by_id(company_id, data.invoice_id)
            if not invoice:
                raise NotFoundError("Invoice not found")
            if invoice.status not in {InvoiceStatus.OVERDUE, InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID}:
                raise ConflictError("Invoice is not eligible for reminders", code=ErrorCode.CONFLICT)

            last = await uow.reminders.last_sent_for_invoice(invoice.id)
            if last and last.sent_at:
                cooldown = timedelta(hours=REMINDER_COOLDOWN_HOURS)
                if datetime.now(timezone.utc) - last.sent_at.replace(tzinfo=timezone.utc) < cooldown:
                    raise ConflictError(
                        f"Reminder cooldown active ({REMINDER_COOLDOWN_HOURS}h)",
                        code=ErrorCode.CONFLICT,
                    )

            customer = await uow.customers.get_by_id(company_id, invoice.customer_id)
            if not customer:
                raise NotFoundError("Customer not found")

            days = (date.today() - invoice.due_date).days
            if data.language == "hi":
                message = (
                    f"नमस्ते {customer.name}, आपका बिल {invoice.invoice_number} "
                    f"₹{invoice.amount_due.amount} बकाया है ({days} दिन)। कृपया भुगतान करें।"
                )
            else:
                message = (
                    f"Hi {customer.name}, invoice {invoice.invoice_number} has "
                    f"₹{invoice.amount_due.amount} due ({days} days overdue). Please pay at earliest."
                )

            reminder = ReminderRecord(
                company_id=company_id,
                invoice_id=invoice.id,
                customer_id=customer.id,
                channel=data.channel,
                message=message,
                sent_by=actor_id,
            )
            saved = await uow.reminders.create(reminder)
            try:
                provider_id = await self._notifier.send_message(
                    channel=data.channel,
                    to=customer.phone.e164,
                    message=message,
                )
                saved = await uow.reminders.update_status(
                    saved.id,
                    status=ReminderStatus.SENT,
                    provider_message_id=provider_id,
                )
            except Exception as exc:
                saved = await uow.reminders.update_status(
                    saved.id,
                    status=ReminderStatus.FAILED,
                    error=str(exc),
                )
                raise

            await uow.audit.log(
                company_id=company_id,
                actor_user_id=actor_id,
                entity_type=EntityType.REMINDER,
                entity_id=saved.id,
                action=AuditAction.REMINDER_SENT,
                before=None,
                after={"invoice_id": str(invoice.id), "status": saved.status},
                ip_address=ip,
            )
            return saved

    async def bulk_preview(self, company_id: uuid.UUID) -> dict:
        overdue = await self.list_overdue(company_id)
        total = sum((r["invoice"].amount_due.amount for r in overdue), start=0)
        return {"count": len(overdue), "total_outstanding": total, "invoices": overdue}

    async def bulk_send(
        self,
        *,
        company_id: uuid.UUID,
        actor_id: uuid.UUID,
        ip: str | None = None,
    ) -> list[ReminderRecord]:
        preview = await self.bulk_preview(company_id)
        results = []
        for item in preview["invoices"]:
            reminder = await self.send_reminder(
                company_id=company_id,
                actor_id=actor_id,
                data=SendReminderInput(invoice_id=item["invoice"].id),
                ip=ip,
            )
            results.append(reminder)
        return results
