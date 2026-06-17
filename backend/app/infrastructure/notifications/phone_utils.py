"""Normalize phone numbers from WhatsApp Cloud API payloads."""
from __future__ import annotations

import re

from app.core.constants import INDIA_COUNTRY_CODE, INDIA_PHONE_REGEX

_DIGITS = re.compile(r"\d+")
_INDIAN_MOBILE = re.compile(INDIA_PHONE_REGEX)


def normalize_whatsapp_phone(raw: str | None) -> str | None:
    """Return 10-digit Indian mobile or None when the sender cannot be matched."""
    if not raw:
        return None
    digits = "".join(_DIGITS.findall(raw))
    if digits.startswith(INDIA_COUNTRY_CODE) and len(digits) == 12:
        digits = digits[len(INDIA_COUNTRY_CODE) :]
    if _INDIAN_MOBILE.match(digits):
        return digits
    return None
