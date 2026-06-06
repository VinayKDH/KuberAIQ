"""Invoice numbering policy: financial-year derivation and number formatting.

Sequence allocation (the gap-free counter) is an infrastructure concern handled inside a
transaction by the repository; this domain service owns the pure formatting rules.
"""
from __future__ import annotations

from datetime import date

from app.core.constants import (
    FINANCIAL_YEAR_START_MONTH,
    INVOICE_NUMBER_PAD,
)


def financial_year(d: date) -> str:
    """Indian FY label, e.g. a date in 2026-06 → '2026-27'; 2026-02 → '2025-26'."""
    if d.month >= FINANCIAL_YEAR_START_MONTH:
        start = d.year
    else:
        start = d.year - 1
    return f"{start}-{str(start + 1)[-2:]}"


def format_invoice_number(prefix: str, fy: str, sequence: int) -> str:
    return f"{prefix}/{fy}/{sequence:0{INVOICE_NUMBER_PAD}d}"
