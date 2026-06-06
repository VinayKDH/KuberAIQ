"""Invoice numbering domain tests."""
from __future__ import annotations

from datetime import date

from app.domain.services.invoice_numbering import financial_year, format_invoice_number


def test_financial_year_april_boundary() -> None:
    assert financial_year(date(2026, 3, 31)) == "2025-26"
    assert financial_year(date(2026, 4, 1)) == "2026-27"


def test_format_invoice_number() -> None:
    assert format_invoice_number("INV", "2025-26", 42) == "INV/2025-26/0042"
