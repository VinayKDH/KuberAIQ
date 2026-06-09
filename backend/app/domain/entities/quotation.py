"""Quotation aggregate root with lifecycle rules."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from app.core.constants import DEFAULT_UNIT
from app.domain.enums import QuotationStatus
from app.domain.exceptions import InvalidStateTransition
from app.domain.services.gst_calculator import GstCalculator, LineInput
from app.domain.value_objects.money import Money


@dataclass
class QuotationItem:
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
class Quotation:
    company_id: uuid.UUID
    customer_id: uuid.UUID
    issue_date: date
    valid_until: date
    items: list[QuotationItem]
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    quotation_number: str | None = None
    financial_year: str | None = None
    status: QuotationStatus = QuotationStatus.DRAFT
    place_of_supply: str | None = None
    pdf_blob_path: str | None = None
    converted_invoice_id: uuid.UUID | None = None
    created_by: uuid.UUID | None = None

    taxable_amount: Money = field(default_factory=Money.zero)
    cgst_amount: Money = field(default_factory=Money.zero)
    sgst_amount: Money = field(default_factory=Money.zero)
    igst_amount: Money = field(default_factory=Money.zero)
    total_tax: Money = field(default_factory=Money.zero)
    round_off: Money = field(default_factory=Money.zero)
    grand_total: Money = field(default_factory=Money.zero)

    def recalculate(self, *, supplier_state: str, customer_state: str | None) -> None:
        lines = [
            LineInput(quantity=i.quantity, unit_price=i.unit_price, gst_rate=i.gst_rate)
            for i in self.items
        ]
        per_line, agg = GstCalculator.aggregate(
            lines, supplier_state=supplier_state, customer_state=customer_state
        )
        for item, breakdown in zip(self.items, per_line, strict=True):
            item.taxable_amount = breakdown.taxable
            item.cgst_amount = breakdown.cgst
            item.sgst_amount = breakdown.sgst
            item.igst_amount = breakdown.igst
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
            raise InvalidStateTransition(f"Quotation in status {self.status} cannot be edited")

    def assign_number(self, *, number: str, fy: str) -> None:
        if self.status != QuotationStatus.DRAFT:
            raise InvalidStateTransition("Only DRAFT quotations can be numbered")
        self.quotation_number = number
        self.financial_year = fy

    def send(self) -> None:
        if self.status != QuotationStatus.DRAFT:
            raise InvalidStateTransition("Only DRAFT quotations can be sent")
        self.status = QuotationStatus.SENT

    def accept(self) -> None:
        if self.status not in {QuotationStatus.SENT, QuotationStatus.DRAFT}:
            raise InvalidStateTransition("Only sent or draft quotations can be accepted")
        self.status = QuotationStatus.ACCEPTED

    def reject(self) -> None:
        if self.status not in {QuotationStatus.SENT, QuotationStatus.DRAFT}:
            raise InvalidStateTransition("Only sent or draft quotations can be rejected")
        self.status = QuotationStatus.REJECTED

    def mark_expired(self) -> None:
        if self.status in {QuotationStatus.CONVERTED, QuotationStatus.REJECTED}:
            raise InvalidStateTransition(f"Cannot expire a {self.status} quotation")
        self.status = QuotationStatus.EXPIRED

    def mark_converted(self, invoice_id: uuid.UUID) -> None:
        if self.status in {QuotationStatus.CONVERTED, QuotationStatus.REJECTED, QuotationStatus.EXPIRED}:
            raise InvalidStateTransition(f"Cannot convert a {self.status} quotation")
        self.status = QuotationStatus.CONVERTED
        self.converted_invoice_id = invoice_id

    def can_convert(self) -> bool:
        return self.status in {
            QuotationStatus.DRAFT,
            QuotationStatus.SENT,
            QuotationStatus.ACCEPTED,
        }
