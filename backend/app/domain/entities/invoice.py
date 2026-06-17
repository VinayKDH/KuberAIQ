"""Invoice aggregate root with InvoiceItem entities and lifecycle rules."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal

from app.core.constants import DEFAULT_UNIT
from app.domain.enums import DocumentType, InvoiceStatus
from app.domain.exceptions import (
    InvalidStateTransition,
    InvoiceHasPayments,
    InvoiceNotEditable,
    PaymentExceedsDue,
)
from app.domain.services.gst_calculator import GstCalculator, LineInput
from app.domain.value_objects.money import Money


@dataclass
class InvoiceItem:
    description: str
    quantity: Decimal
    unit_price: Money
    gst_rate: Decimal
    line_no: int
    hsn_sac: str | None = None
    unit: str = DEFAULT_UNIT
    product_id: uuid.UUID | None = None
    taxable_amount: Money = field(default_factory=Money.zero)
    cgst_amount: Money = field(default_factory=Money.zero)
    sgst_amount: Money = field(default_factory=Money.zero)
    igst_amount: Money = field(default_factory=Money.zero)

    @property
    def line_total(self) -> Money:
        return self.taxable_amount + self.cgst_amount + self.sgst_amount + self.igst_amount


@dataclass
class Invoice:
    company_id: uuid.UUID
    customer_id: uuid.UUID
    issue_date: date
    due_date: date
    items: list[InvoiceItem]
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    invoice_number: str | None = None
    financial_year: str | None = None
    status: InvoiceStatus = InvoiceStatus.DRAFT
    place_of_supply: str | None = None
    cancel_reason: str | None = None
    pdf_blob_path: str | None = None
    payment_link_url: str | None = None
    created_by: uuid.UUID | None = None
    irn: str | None = None
    irn_generated_at: datetime | None = None
    document_type: DocumentType = DocumentType.INVOICE
    original_invoice_id: uuid.UUID | None = None
    credit_reason: str | None = None

    taxable_amount: Money = field(default_factory=Money.zero)
    cgst_amount: Money = field(default_factory=Money.zero)
    sgst_amount: Money = field(default_factory=Money.zero)
    igst_amount: Money = field(default_factory=Money.zero)
    total_tax: Money = field(default_factory=Money.zero)
    round_off: Money = field(default_factory=Money.zero)
    grand_total: Money = field(default_factory=Money.zero)
    amount_paid: Money = field(default_factory=Money.zero)

    @property
    def amount_due(self) -> Money:
        if self.document_type != DocumentType.INVOICE:
            return Money.zero()
        return self.grand_total - self.amount_paid

    # --- behaviour ---------------------------------------------------------
    def recalculate(self, *, supplier_state: str, customer_state: str | None) -> None:
        """Recompute all tax fields from items via the GST domain service."""
        lines = [
            LineInput(quantity=i.quantity, unit_price=i.unit_price, gst_rate=i.gst_rate)
            for i in self.items
        ]
        per_line, agg = GstCalculator.aggregate(
            lines, supplier_state=supplier_state, customer_state=customer_state
        )
        for item, b in zip(self.items, per_line, strict=True):
            item.taxable_amount = b.taxable
            item.cgst_amount = b.cgst
            item.sgst_amount = b.sgst
            item.igst_amount = b.igst
        self.taxable_amount = agg.taxable
        self.cgst_amount = agg.cgst
        self.sgst_amount = agg.sgst
        self.igst_amount = agg.igst
        self.total_tax = agg.total_tax
        rounded, adjustment = GstCalculator.round_off(agg.total)
        self.round_off = adjustment
        self.grand_total = rounded
        self.place_of_supply = customer_state or supplier_state

    def ensure_editable(self) -> None:
        if not self.status.is_editable:
            raise InvoiceNotEditable(
                f"Invoice in status {self.status} cannot be edited"
            )

    def issue(self, *, number: str, fy: str) -> None:
        if self.status is not InvoiceStatus.DRAFT:
            raise InvalidStateTransition("Only DRAFT invoices can be issued")
        self.invoice_number = number
        self.financial_year = fy
        self.status = InvoiceStatus.ISSUED

    def cancel(self, reason: str) -> None:
        if not self.amount_paid.is_zero:
            raise InvoiceHasPayments("Cannot cancel an invoice with recorded payments")
        if self.status in {InvoiceStatus.PAID, InvoiceStatus.CANCELLED}:
            raise InvalidStateTransition(f"Cannot cancel a {self.status} invoice")
        if not reason.strip():
            raise ValueError("Cancellation reason is required")
        self.status = InvoiceStatus.CANCELLED
        self.cancel_reason = reason.strip()

    def apply_payment(self, amount: Money) -> None:
        if amount.is_negative or amount.is_zero:
            raise ValueError("Payment amount must be positive")
        if amount.amount > self.amount_due.amount:
            raise PaymentExceedsDue("Payment exceeds the outstanding balance")
        self.amount_paid = self.amount_paid + amount
        self._sync_status_after_payment_change()

    def reverse_payment(self, amount: Money, *, today: date) -> None:
        if self.status is InvoiceStatus.CANCELLED:
            raise InvalidStateTransition("Cannot reverse payment on a cancelled invoice")
        if amount.is_negative or amount.is_zero:
            raise ValueError("Reversal amount must be positive")
        if amount.amount > self.amount_paid.amount:
            raise PaymentExceedsDue("Reversal exceeds recorded payments")
        self.amount_paid = self.amount_paid - amount
        self._sync_status_after_payment_change(today=today)

    def _sync_status_after_payment_change(self, *, today: date | None = None) -> None:
        if self.amount_due.is_zero:
            self.status = InvoiceStatus.PAID
        elif not self.amount_paid.is_zero:
            self.status = InvoiceStatus.PARTIALLY_PAID
        elif today and self.due_date < today:
            self.status = InvoiceStatus.OVERDUE
        else:
            self.status = InvoiceStatus.ISSUED

    def mark_overdue_if_due(self, today: date) -> bool:
        if self.status in {InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID} and (
            self.due_date < today and not self.amount_due.is_zero
        ):
            self.status = InvoiceStatus.OVERDUE
            return True
        return False

    def apply_credit(self, amount: Money) -> None:
        """Reduce outstanding when a credit note is issued against this invoice."""
        if self.document_type != DocumentType.INVOICE:
            raise InvalidStateTransition("Credits can only be applied to tax invoices")
        if self.status in {InvoiceStatus.DRAFT, InvoiceStatus.CANCELLED, InvoiceStatus.PAID}:
            raise InvalidStateTransition(f"Cannot apply credit to a {self.status} invoice")
        if amount.is_negative or amount.is_zero:
            raise ValueError("Credit amount must be positive")
        if amount.amount > self.amount_due.amount:
            raise PaymentExceedsDue("Credit exceeds the outstanding balance")
        self.amount_paid = self.amount_paid + amount
        self._sync_status_after_payment_change()

    def register_irn(self, irn: str, *, generated_at: datetime | None = None) -> None:
        if self.status in {InvoiceStatus.DRAFT, InvoiceStatus.CANCELLED}:
            raise InvalidStateTransition("Cannot register IRN on draft or cancelled invoices")
        cleaned = irn.strip().upper()
        if len(cleaned) < 10:
            raise ValueError("IRN must be at least 10 characters")
        self.irn = cleaned
        self.irn_generated_at = generated_at or datetime.now(timezone.utc)
