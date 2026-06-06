"""AI guardrails — injection filtering and output validation."""
from __future__ import annotations

import re
from typing import Any

from app.core.constants import AI_RESPONSE_MAX_LEN, GST_TOLERANCE

_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"you\s+are\s+now",
    r"system\s+prompt",
    r"<\s*script",
]


def filter_injection(text: str) -> str:
    cleaned = text.strip()
    for pattern in _INJECTION_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    return cleaned[:2000]


def validate_response(response: dict[str, Any]) -> dict[str, Any]:
    required = {"intent", "message", "requires_confirmation"}
    if not required.issubset(response.keys()):
        return {
            "intent": "clarify",
            "message": "I couldn't process that request. Please try again.",
            "requires_confirmation": False,
            "pending_action": None,
            "data": None,
            "suggested_actions": [],
        }
    if len(response.get("message", "")) > AI_RESPONSE_MAX_LEN:
        response["message"] = response["message"][:AI_RESPONSE_MAX_LEN]
    return response


def validate_gst_totals(
    taxable: float, cgst: float, sgst: float, igst: float, total_tax: float
) -> bool:
    computed = cgst + sgst + igst
    return abs(computed - total_tax) <= float(GST_TOLERANCE)
