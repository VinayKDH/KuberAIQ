"""PDF formatting helpers — currency display and amount in words."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from app.core.constants import CURRENCY_SYMBOL, PDF_CURRENCY_PREFIX

_ONES = (
    "",
    "One",
    "Two",
    "Three",
    "Four",
    "Five",
    "Six",
    "Seven",
    "Eight",
    "Nine",
    "Ten",
    "Eleven",
    "Twelve",
    "Thirteen",
    "Fourteen",
    "Fifteen",
    "Sixteen",
    "Seventeen",
    "Eighteen",
    "Nineteen",
)
_TENS = ("", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety")


def format_inr(value: float | Decimal | int) -> str:
    amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{CURRENCY_SYMBOL}{amount:,.2f}"


def format_inr_pdf(value: float | Decimal | int) -> str:
    """Currency formatting for PDF output (Helvetica lacks the ₹ glyph)."""
    amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{PDF_CURRENCY_PREFIX}{amount:,.2f}"


def _two_digits(n: int) -> str:
    if n < 20:
        return _ONES[n]
    tens, ones = divmod(n, 10)
    return f"{_TENS[tens]}{' ' + _ONES[ones] if ones else ''}".strip()


def _indian_group(n: int) -> str:
    if n == 0:
        return ""
    if n < 100:
        return _two_digits(n)
    if n < 1000:
        hundreds, rem = divmod(n, 100)
        head = f"{_ONES[hundreds]} Hundred"
        tail = _two_digits(rem)
        return f"{head}{' ' + tail if tail else ''}".strip()
    return ""


def _integer_to_words(n: int) -> str:
    if n == 0:
        return "Zero"
    parts: list[str] = []
    crore, n = divmod(n, 10_000_000)
    lakh, n = divmod(n, 100_000)
    thousand, n = divmod(n, 1000)
    if crore:
        parts.append(f"{_integer_to_words(crore)} Crore")
    if lakh:
        parts.append(f"{_two_digits(lakh)} Lakh" if lakh < 100 else f"{_integer_to_words(lakh)} Lakh")
    if thousand:
        parts.append(f"{_two_digits(thousand)} Thousand" if thousand < 100 else f"{_integer_to_words(thousand)} Thousand")
    rest = _indian_group(n)
    if rest:
        parts.append(rest)
    return " ".join(parts)


def amount_to_words_inr(value: float | Decimal) -> str:
    amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    rupees = int(amount)
    paise = int((amount - rupees) * 100)
    words = _integer_to_words(rupees)
    if paise:
        return f"Rupees {words} and {paise} Paise only"
    return f"Rupees {words} only"
