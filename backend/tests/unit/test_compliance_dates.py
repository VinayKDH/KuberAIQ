"""Tests for compliance date helpers."""
from __future__ import annotations

from datetime import date

from app.domain.services.compliance_dates import gstr1_due_for_period, gstr3b_due_for_period


def test_gstr1_due_for_june_period() -> None:
    assert gstr1_due_for_period(date(2026, 6, 30)) == date(2026, 7, 11)


def test_gstr3b_due_for_december_period() -> None:
    assert gstr3b_due_for_period(date(2026, 12, 31)) == date(2027, 1, 20)
