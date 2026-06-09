"""Tests for UPI payment link helpers."""
from __future__ import annotations

from decimal import Decimal

from app.domain.services.upi import (
    build_upi_payment_link,
    format_upi_amount,
    normalize_upi_id,
)


def test_normalize_upi_id() -> None:
    assert normalize_upi_id(" Merchant@UPI ") == "merchant@upi"


def test_format_upi_amount() -> None:
    assert format_upi_amount(Decimal("1180.5")) == "1180.50"
    assert format_upi_amount(100) == "100.00"


def test_build_upi_payment_link() -> None:
    link = build_upi_payment_link(
        upi_id="demo@upi",
        payee_name="Demo Traders",
        amount=Decimal("1500"),
        transaction_note="Payment for INV/2025-26/0001",
    )
    assert link.startswith("upi://pay?")
    assert "pa=demo%40upi" in link
    assert "am=1500.00" in link
    assert "cu=INR" in link
