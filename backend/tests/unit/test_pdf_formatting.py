"""Tests for PDF formatting helpers."""
from __future__ import annotations

from app.infrastructure.pdf.formatting import amount_to_words_inr, format_inr, format_inr_pdf


def test_format_inr() -> None:
    assert format_inr(1234.5) == "₹1,234.50"


def test_format_inr_pdf_uses_rs_prefix() -> None:
    assert format_inr_pdf(1234.5) == "Rs. 1,234.50"


def test_amount_to_words_inr() -> None:
    assert amount_to_words_inr(1180) == "Rupees One Thousand One Hundred Eighty only"
    assert "Paise" in amount_to_words_inr(1180.25)
