"""Unit tests for GST calculator domain service."""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.domain.services.gst_calculator import GstCalculator, LineInput
from app.domain.value_objects.money import Money


def test_intra_state_cgst_sgst_split():
    line = LineInput(quantity=Decimal("10"), unit_price=Money.of(100), gst_rate=Decimal("18"))
    breakup = GstCalculator.line_breakup(line, intra_state=True)
    assert breakup.taxable.amount == Decimal("1000.00")
    assert breakup.cgst.amount == Decimal("90.00")
    assert breakup.sgst.amount == Decimal("90.00")
    assert breakup.igst.is_zero


def test_inter_state_igst():
    line = LineInput(quantity=Decimal("5"), unit_price=Money.of(200), gst_rate=Decimal("12"))
    breakup = GstCalculator.line_breakup(line, intra_state=False)
    assert breakup.taxable.amount == Decimal("1000.00")
    assert breakup.igst.amount == Decimal("120.00")
    assert breakup.cgst.is_zero
    assert breakup.sgst.is_zero


def test_aggregate_totals():
    lines = [
        LineInput(quantity=Decimal("50"), unit_price=Money.of(350), gst_rate=Decimal("18")),
    ]
    per_line, agg = GstCalculator.aggregate(lines, supplier_state="27", customer_state="27")
    assert len(per_line) == 1
    assert agg.taxable.amount == Decimal("17500.00")
    assert agg.cgst.amount == Decimal("1575.00")
    assert agg.sgst.amount == Decimal("1575.00")
    assert agg.total_tax.amount == Decimal("3150.00")


def test_round_off():
    total = Money.of("20650.49")
    rounded, adjustment = GstCalculator.round_off(total)
    assert rounded.amount == Decimal("20650")
    assert adjustment.amount == Decimal("-0.49")


def test_invalid_gst_rate_raises():
    line = LineInput(quantity=Decimal("1"), unit_price=Money.of(100), gst_rate=Decimal("7"))
    with pytest.raises(Exception):
        GstCalculator.line_breakup(line, intra_state=True)
