"""Scheduled reminder trigger resolution."""
from __future__ import annotations

from datetime import date

from app.core.constants import (
    REMINDER_OVERDUE_MILESTONES,
    REMINDER_SCHEDULE_DAYS_BEFORE_DUE,
    ReminderTrigger,
)
from app.domain.entities.invoice import Invoice


def resolve_reminder_trigger(invoice: Invoice, today: date) -> str | None:
    if invoice.amount_due.is_zero or not invoice.status.is_open:
        return None

    days_until_due = (invoice.due_date - today).days
    days_overdue = (today - invoice.due_date).days

    if days_until_due == REMINDER_SCHEDULE_DAYS_BEFORE_DUE:
        return ReminderTrigger.DUE_SOON
    if days_until_due == 0:
        return ReminderTrigger.DUE_TODAY
    if days_overdue in REMINDER_OVERDUE_MILESTONES:
        return {
            7: ReminderTrigger.OVERDUE_7,
            15: ReminderTrigger.OVERDUE_15,
            30: ReminderTrigger.OVERDUE_30,
        }[days_overdue]
    return None
