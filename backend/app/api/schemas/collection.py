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


class ReminderPreviewResponse(BaseModel):
    invoice_id: str
    customer_name: str
    days_overdue: int
    amount_due: Decimal
    language: str
    message: str


class OverdueInvoiceResponse(BaseModel):
    id: str
    invoice_id: str
    invoice_number: str | None
    customer_name: str
    customer_phone: str | None = None
    amount_due: Decimal
    days_overdue: int
    due_date: str
    last_reminder_at: str | None = None
    last_reminder_channel: str | None = None


class BulkPreviewResponse(BaseModel):
    count: int
    total_outstanding: Decimal


class CollectionsDashboardResponse(BaseModel):
    overdue_count: int
    total_outstanding: Decimal
    total_overdue: Decimal
    reminded_today: int = 0
    invoices: list[OverdueInvoiceResponse]


class CallTodayInvoiceResponse(BaseModel):
    id: str
    invoice_id: str
    invoice_number: str | None
    customer_name: str
    customer_phone: str | None = None
    amount_due: Decimal
    days_overdue: int
    days_until_due: int
    priority_score: float
    due_date: str
    last_reminder_at: str | None = None
    last_reminder_channel: str | None = None
