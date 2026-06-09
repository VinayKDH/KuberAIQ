"""Tests for scheduled reminder trigger resolution."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.core.constants import REMINDER_SCHEDULE_DAYS_BEFORE_DUE, ReminderTrigger
from app.domain.entities.invoice import Invoice, InvoiceItem
from app.domain.services.reminder_schedule import resolve_reminder_trigger
from app.domain.value_objects.money import Money


def _issued_invoice(*, due_date: date, amount_paid: Decimal = Decimal("0")) -> Invoice:
    item = InvoiceItem(
        line_no=1,
        description="Goods",
        quantity=Decimal("1"),
        unit_price=Money.of(1000),
        gst_rate=Decimal("18"),
    )
    inv = Invoice(
        company_id=__import__("uuid").uuid4(),
        customer_id=__import__("uuid").uuid4(),
        issue_date=due_date,
        due_date=due_date,
        items=[item],
    )
    inv.recalculate(supplier_state="27", customer_state="27")
    inv.issue(number="INV/2026-27/0001", fy="2026-27")
    if amount_paid:
        inv.apply_payment(Money.of(amount_paid))
    return inv


@pytest.mark.parametrize(
    ("due_date", "today", "expected"),
    [
        (
            date(2026, 6, 10),
            date(2026, 6, 7),
            ReminderTrigger.DUE_SOON,
        ),
        (date(2026, 6, 10), date(2026, 6, 10), ReminderTrigger.DUE_TODAY),
        (date(2026, 6, 1), date(2026, 6, 8), ReminderTrigger.OVERDUE_7),
        (date(2026, 6, 1), date(2026, 6, 16), ReminderTrigger.OVERDUE_15),
        (date(2026, 6, 1), date(2026, 7, 1), ReminderTrigger.OVERDUE_30),
    ],
)
def test_resolve_reminder_trigger_milestones(
    due_date: date, today: date, expected: str
) -> None:
    invoice = _issued_invoice(due_date=due_date)
    assert resolve_reminder_trigger(invoice, today) == expected


def test_resolve_reminder_trigger_returns_none_when_paid() -> None:
    due_date = date(2026, 6, 10)
    invoice = _issued_invoice(due_date=due_date)
    invoice.apply_payment(invoice.grand_total)
    assert resolve_reminder_trigger(invoice, date(2026, 6, 10)) is None


def test_resolve_reminder_trigger_returns_none_between_milestones() -> None:
    invoice = _issued_invoice(due_date=date(2026, 6, 1))
    assert resolve_reminder_trigger(invoice, date(2026, 6, 5)) is None


def test_resolve_reminder_trigger_due_soon_uses_schedule_constant() -> None:
    due_date = date(2026, 6, 10)
    today = due_date - timedelta(days=REMINDER_SCHEDULE_DAYS_BEFORE_DUE)
    invoice = _issued_invoice(due_date=due_date)
    assert resolve_reminder_trigger(invoice, today) == ReminderTrigger.DUE_SOON
