"""Deterministic GST calculation — the single source of truth for tax math.

The LLM never computes tax; it only extracts entities. This service is pure and
exhaustively unit-tested.

Rule: if the place of supply (customer state) equals the supplier (company) state,
the tax is intra-state → split into CGST + SGST (each = rate/2). Otherwise it is
inter-state → IGST (full rate).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.core.constants import ALLOWED_GST_RATES
from app.domain.exceptions import InvalidGstRate
from app.domain.value_objects.gst_breakup import GstBreakup
from app.domain.value_objects.money import Money


@dataclass(frozen=True, slots=True)
class LineInput:
    quantity: Decimal
    unit_price: Money
    gst_rate: Decimal  # whole-number percentage, e.g. 18


def _validate_rate(rate: Decimal) -> None:
    if rate not in ALLOWED_GST_RATES:
        allowed = ", ".join(str(r) for r in ALLOWED_GST_RATES)
        raise InvalidGstRate(f"GST rate {rate}% not allowed. Allowed: {allowed}")


class GstCalculator:
    """Stateless domain service."""

    @staticmethod
    def line_breakup(line: LineInput, *, intra_state: bool) -> GstBreakup:
        _validate_rate(line.gst_rate)
        taxable = line.unit_price * line.quantity
        tax_total = taxable * (line.gst_rate / Decimal("100"))
        if intra_state:
            half = tax_total * Decimal("0.5")
            return GstBreakup(
                taxable=taxable,
                cgst=Money.of(half.amount),
                sgst=Money.of(half.amount),
                igst=Money.zero(),
            )
        return GstBreakup(
            taxable=taxable,
            cgst=Money.zero(),
            sgst=Money.zero(),
            igst=Money.of(tax_total.amount),
        )

    @classmethod
    def aggregate(
        cls, lines: list[LineInput], *, supplier_state: str, customer_state: str | None
    ) -> tuple[list[GstBreakup], GstBreakup]:
        """Return per-line breakups plus the invoice-level aggregate.

        If the customer state is unknown we conservatively treat it as intra-state
        (most MSME sales are local); callers should supply the customer state when known.
        """
        intra_state = customer_state is None or customer_state == supplier_state
        per_line = [cls.line_breakup(ln, intra_state=intra_state) for ln in lines]
        taxable = Money.zero()
        cgst = Money.zero()
        sgst = Money.zero()
        igst = Money.zero()
        for b in per_line:
            taxable = taxable + b.taxable
            cgst = cgst + b.cgst
            sgst = sgst + b.sgst
            igst = igst + b.igst
        return per_line, GstBreakup(taxable=taxable, cgst=cgst, sgst=sgst, igst=igst)

    @staticmethod
    def round_off(grand_total: Money) -> tuple[Money, Money]:
        """Round the grand total to the nearest rupee; return (rounded, adjustment)."""
        rounded = grand_total.amount.quantize(Decimal("1"))
        adjustment = rounded - grand_total.amount
        return Money.of(rounded), Money.of(adjustment)
