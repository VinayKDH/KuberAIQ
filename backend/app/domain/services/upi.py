"""UPI deep-link helpers for invoice payments."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import quote

from app.core.constants import UPI_CURRENCY


def normalize_upi_id(upi_id: str) -> str:
    return upi_id.strip().lower()


def format_upi_amount(value: Decimal | float | int) -> str:
    amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{amount:.2f}"


def build_upi_payment_link(
    *,
    upi_id: str,
    payee_name: str,
    amount: Decimal | float | int,
    transaction_note: str,
) -> str:
    params = {
        "pa": normalize_upi_id(upi_id),
        "pn": payee_name.strip()[:100],
        "am": format_upi_amount(amount),
        "cu": UPI_CURRENCY,
        "tn": transaction_note.strip()[:120],
    }
    query = "&".join(f"{key}={quote(str(value))}" for key, value in params.items())
    return f"upi://pay?{query}"
