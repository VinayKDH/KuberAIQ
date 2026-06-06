"""Collections API schemas."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

from app.domain.enums import ReminderChannel, ReminderStatus


class SendReminderRequest(BaseModel):
    invoice_id: str
    channel: ReminderChannel = ReminderChannel.WHATSAPP
    language: str = "en"


class ReminderResponse(BaseModel):
    reminder_id: str
    status: ReminderStatus
    provider_message_id: str | None = None


class OverdueInvoiceResponse(BaseModel):
    invoice_id: str
    invoice_number: str | None
    customer_name: str
    amount_due: Decimal
    days_overdue: int
    due_date: str


class BulkPreviewResponse(BaseModel):
    count: int
    total_outstanding: Decimal


class CollectionsDashboardResponse(BaseModel):
    overdue_count: int
    total_outstanding: Decimal
    invoices: list[OverdueInvoiceResponse]
