"""Invoice aggregate domain tests."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.domain.entities.invoice import Invoice, InvoiceItem
from app.domain.enums import InvoiceStatus
from app.domain.exceptions import InvoiceHasPayments, InvoiceNotEditable, PaymentExceedsDue
from app.domain.value_objects.money import Money


def _draft_invoice() -> Invoice:
    item = InvoiceItem(
        line_no=1,
        description="Cement",
        quantity=Decimal("10"),
        unit_price=Money.of(100),
        gst_rate=Decimal("18"),
    )
    inv = Invoice(
        company_id=__import__("uuid").uuid4(),
        customer_id=__import__("uuid").uuid4(),
        issue_date=date(2026, 6, 6),
        due_date=date(2026, 6, 21),
        items=[item],
    )
    inv.recalculate(supplier_state="27", customer_state="27")
    return inv


def test_recalculate_intrastate_gst() -> None:
    inv = _draft_invoice()
    assert inv.cgst_amount.amount > 0
    assert inv.igst_amount.is_zero
    assert inv.grand_total.amount > inv.taxable_amount.amount


def test_issue_and_cancel() -> None:
    inv = _draft_invoice()
    inv.issue(number="INV/2026-27/0001", fy="2026-27")
    assert inv.status == InvoiceStatus.ISSUED
    inv.cancel("Mistake")
    assert inv.status == InvoiceStatus.CANCELLED


def test_apply_payment_updates_status() -> None:
    inv = _draft_invoice()
    inv.issue(number="INV/2026-27/0001", fy="2026-27")
    inv.apply_payment(inv.grand_total)
    assert inv.status == InvoiceStatus.PAID


def test_cannot_edit_issued_invoice() -> None:
    inv = _draft_invoice()
    inv.issue(number="INV/2026-27/0001", fy="2026-27")
    with pytest.raises(InvoiceNotEditable):
        inv.ensure_editable()


def test_payment_exceeds_due() -> None:
    inv = _draft_invoice()
    inv.issue(number="INV/2026-27/0001", fy="2026-27")
    with pytest.raises(PaymentExceedsDue):
        inv.apply_payment(Money.of(999999))


def test_mark_overdue_if_due() -> None:
    inv = _draft_invoice()
    inv.issue(number="INV/2026-27/0001", fy="2026-27")
    changed = inv.mark_overdue_if_due(date(2026, 7, 1))
    assert changed is True
    assert inv.status == InvoiceStatus.OVERDUE


def test_cannot_cancel_with_payments() -> None:
    inv = _draft_invoice()
    inv.issue(number="INV/2026-27/0001", fy="2026-27")
    inv.apply_payment(Money.of(100))
    with pytest.raises(InvoiceHasPayments):
        inv.cancel("Too late")


def test_reverse_payment_restores_outstanding() -> None:
    inv = _draft_invoice()
    inv.issue(number="INV/2026-27/0001", fy="2026-27")
    partial = Money.of(100)
    inv.apply_payment(partial)
    assert inv.status == InvoiceStatus.PARTIALLY_PAID
    inv.reverse_payment(partial, today=date(2026, 6, 10))
    assert inv.amount_paid.is_zero
    assert inv.status == InvoiceStatus.ISSUED
