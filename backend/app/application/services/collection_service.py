"""Collections use-case orchestration."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import structlog

from app.application.ports.notifier import NotifierPort
from app.application.ports.repositories import ReminderRecord
from app.core.constants import (
    CALL_TODAY_LIMIT,
    DEFAULT_REMINDER_LANGUAGE,
    REMINDER_COOLDOWN_HOURS,
    REMINDER_SCHEDULE_DAYS_BEFORE_DUE,
    WHATSAPP_REMINDER_BODY,
    WHATSAPP_TEMPLATE_REMINDER_EN,
    WHATSAPP_TEMPLATE_REMINDER_HI,
    AuditAction,
    EntityType,
    ErrorCode,
    ReminderTrigger,
)
from app.core.errors import ConflictError, NotFoundError
from app.domain.enums import InvoiceStatus, ReminderChannel, ReminderStatus
from app.domain.services.reminder_schedule import resolve_reminder_trigger

logger = structlog.get_logger(__name__)


@dataclass
class SendReminderInput:
    invoice_id: uuid.UUID
    channel: ReminderChannel = ReminderChannel.WHATSAPP
    language: str = "en"
    trigger: str = ReminderTrigger.MANUAL


class CollectionService:
    def __init__(self, uow_factory, notifier: NotifierPort) -> None:
        self._uow_factory = uow_factory
        self._notifier = notifier

    @staticmethod
    def _fallback_channels(primary: ReminderChannel) -> list[ReminderChannel]:
        if primary == ReminderChannel.WHATSAPP:
            return [ReminderChannel.WHATSAPP, ReminderChannel.SMS, ReminderChannel.EMAIL]
        if primary == ReminderChannel.SMS:
            return [ReminderChannel.SMS, ReminderChannel.EMAIL]
        return [ReminderChannel.EMAIL]

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
                        "customer_phone": customer.phone.value if customer else None,
                        "days_overdue": max((today - inv.due_date).days, 0),
                        "last_reminder": last,
                    }
                )
            results.sort(key=lambda r: (-r["invoice"].amount_due.amount, -r["days_overdue"]))
            return results

    async def list_unpaid(self, company_id: uuid.UUID) -> list[dict]:
        async with self._uow_factory() as uow:
            invoices = await uow.invoices.list_collectible(company_id)
            today = date.today()
            results = []
            for inv in invoices:
                customer = await uow.customers.get_by_id(company_id, inv.customer_id)
                days_overdue = max((today - inv.due_date).days, 0)
                results.append(
                    {
                        "invoice": inv,
                        "customer_name": customer.name if customer else "Unknown",
                        "customer_phone": customer.phone.value if customer else None,
                        "days_overdue": days_overdue,
                        "is_overdue": days_overdue > 0,
                    }
                )
            results.sort(key=lambda r: (-r["invoice"].amount_due.amount, -r["days_overdue"]))
            return results

    async def list_call_today(self, company_id: uuid.UUID) -> list[dict]:
        today = date.today()
        async with self._uow_factory() as uow:
            invoices = await uow.invoices.list_collectible(company_id)
            rows: list[dict] = []
            for inv in invoices:
                days_until_due = (inv.due_date - today).days
                days_overdue = max((today - inv.due_date).days, 0)
                if days_until_due > REMINDER_SCHEDULE_DAYS_BEFORE_DUE:
                    continue
                customer = await uow.customers.get_by_id(company_id, inv.customer_id)
                priority = float(inv.amount_due.amount) * max(1, days_overdue + 1)
                rows.append(
                    {
                        "invoice": inv,
                        "customer_name": customer.name if customer else "Unknown",
                        "customer_phone": customer.phone.value if customer else None,
                        "days_overdue": days_overdue,
                        "days_until_due": days_until_due,
                        "priority_score": priority,
                        "last_reminder": await uow.reminders.last_sent_for_invoice(inv.id),
                    }
                )
            rows.sort(key=lambda row: (-row["priority_score"], row["days_until_due"]))
            return rows[:CALL_TODAY_LIMIT]

    def build_reminder_message(
        self,
        *,
        customer_name: str,
        invoice_number: str | None,
        amount_due,
        days_overdue: int,
        language: str = "en",
        trigger: str = ReminderTrigger.MANUAL,
        days_until_due: int | None = None,
    ) -> str:
        number = invoice_number or "invoice"
        lang = "hi" if language == "hi" else "en"
        if trigger == ReminderTrigger.DUE_SOON:
            days = days_until_due or REMINDER_SCHEDULE_DAYS_BEFORE_DUE
            return WHATSAPP_REMINDER_BODY["due_soon"][lang].format(
                customer_name=customer_name,
                invoice_number=number,
                amount_due=amount_due,
                days=days,
            )
        if trigger == ReminderTrigger.DUE_TODAY:
            return WHATSAPP_REMINDER_BODY["due_today"][lang].format(
                customer_name=customer_name,
                invoice_number=number,
                amount_due=amount_due,
            )
        return WHATSAPP_REMINDER_BODY["overdue"][lang].format(
            customer_name=customer_name,
            invoice_number=number,
            amount_due=amount_due,
            days_overdue=days_overdue,
        )

    async def preview_reminder(
        self,
        company_id: uuid.UUID,
        invoice_id: uuid.UUID,
        *,
        language: str = "en",
    ) -> dict:
        async with self._uow_factory() as uow:
            invoice = await uow.invoices.get_by_id(company_id, invoice_id)
            if not invoice:
                raise NotFoundError("Invoice not found")
            customer = await uow.customers.get_by_id(company_id, invoice.customer_id)
            if not customer:
                raise NotFoundError("Customer not found")
            today = date.today()
            days_overdue = max((today - invoice.due_date).days, 0)
            days_until_due = (invoice.due_date - today).days
            trigger = resolve_reminder_trigger(invoice, today) or ReminderTrigger.MANUAL
            message = self.build_reminder_message(
                customer_name=customer.name,
                invoice_number=invoice.invoice_number,
                amount_due=invoice.amount_due.amount,
                days_overdue=days_overdue,
                language=language,
                trigger=trigger,
                days_until_due=days_until_due,
            )
            return {
                "invoice_id": str(invoice.id),
                "customer_name": customer.name,
                "days_overdue": days_overdue,
                "amount_due": invoice.amount_due.amount,
                "language": language,
                "message": message,
            }

    async def send_reminder(
        self,
        *,
        company_id: uuid.UUID,
        actor_id: uuid.UUID | None,
        data: SendReminderInput,
        ip: str | None = None,
        automated: bool = False,
    ) -> ReminderRecord:
        async with self._uow_factory() as uow:
            invoice = await uow.invoices.get_by_id(company_id, data.invoice_id)
            if not invoice:
                raise NotFoundError("Invoice not found")
            if invoice.status not in {InvoiceStatus.OVERDUE, InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID}:
                raise ConflictError("Invoice is not eligible for reminders", code=ErrorCode.CONFLICT)

            if not automated:
                last = await uow.reminders.last_sent_for_invoice(invoice.id)
                if last and last.sent_at:
                    cooldown = timedelta(hours=REMINDER_COOLDOWN_HOURS)
                    if datetime.now(timezone.utc) - last.sent_at.replace(tzinfo=timezone.utc) < cooldown:
                        raise ConflictError(
                            f"Reminder cooldown active ({REMINDER_COOLDOWN_HOURS}h)",
                            code=ErrorCode.CONFLICT,
                        )
            elif await uow.reminders.has_sent_trigger(invoice.id, data.trigger):
                raise ConflictError("Scheduled reminder already sent", code=ErrorCode.CONFLICT)

            customer = await uow.customers.get_by_id(company_id, invoice.customer_id)
            if not customer:
                raise NotFoundError("Customer not found")

            today = date.today()
            days_overdue = max((today - invoice.due_date).days, 0)
            days_until_due = (invoice.due_date - today).days
            message = self.build_reminder_message(
                customer_name=customer.name,
                invoice_number=invoice.invoice_number,
                amount_due=invoice.amount_due.amount,
                days_overdue=days_overdue,
                language=data.language,
                trigger=data.trigger,
                days_until_due=days_until_due,
            )

            reminder = ReminderRecord(
                company_id=company_id,
                invoice_id=invoice.id,
                customer_id=customer.id,
                channel=data.channel,
                message=message,
                sent_by=actor_id,
                trigger=data.trigger,
            )
            saved = await uow.reminders.create(reminder)
            try:
                template_name = (
                    WHATSAPP_TEMPLATE_REMINDER_HI
                    if data.language == "hi"
                    else WHATSAPP_TEMPLATE_REMINDER_EN
                )
                provider_id = None
                last_error: Exception | None = None
                for channel in self._fallback_channels(data.channel):
                    try:
                        provider_id = await self._notifier.send_message(
                            channel=channel,
                            to=customer.phone.e164 if channel != ReminderChannel.EMAIL else (customer.email or customer.phone.e164),
                            message=message,
                            template_name=template_name if channel == ReminderChannel.WHATSAPP else None,
                        )
                        saved.channel = channel
                        break
                    except Exception as exc:  # pragma: no cover - fallback path
                        last_error = exc
                        continue
                if not provider_id and last_error:
                    raise last_error
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
                after={
                    "invoice_id": str(invoice.id),
                    "status": saved.status,
                    "trigger": data.trigger,
                    "automated": automated,
                },
                ip_address=ip,
            )
            return saved

    async def send_scheduled_reminders(self, company_id: uuid.UUID) -> int:
        today = date.today()
        sent = 0
        async with self._uow_factory() as uow:
            company = await uow.companies.get_by_id(company_id)
            if not company or not company.auto_reminders_enabled:
                return 0
            invoices = await uow.invoices.list_collectible(company_id)

        for invoice in invoices:
            trigger = resolve_reminder_trigger(invoice, today)
            if not trigger:
                continue
            try:
                await self.send_reminder(
                    company_id=company_id,
                    actor_id=None,
                    data=SendReminderInput(
                        invoice_id=invoice.id,
                        language=company.default_reminder_language,
                        trigger=trigger,
                    ),
                    automated=True,
                )
                sent += 1
            except ConflictError:
                continue
            except Exception as exc:
                logger.warning(
                    "scheduled_reminder_failed",
                    company_id=str(company_id),
                    invoice_id=str(invoice.id),
                    trigger=trigger,
                    error=str(exc),
                )
        return sent

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
        async with self._uow_factory() as uow:
            company = await uow.companies.get_by_id(company_id)
        language = (
            company.default_reminder_language
            if company and company.default_reminder_language
            else DEFAULT_REMINDER_LANGUAGE
        )
        preview = await self.bulk_preview(company_id)
        results = []
        for item in preview["invoices"]:
            reminder = await self.send_reminder(
                company_id=company_id,
                actor_id=actor_id,
                data=SendReminderInput(invoice_id=item["invoice"].id, language=language),
                ip=ip,
            )
            results.append(reminder)
        return results
