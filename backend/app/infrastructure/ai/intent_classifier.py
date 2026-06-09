"""Rule-based intent routing — reliable fallback when Azure OpenAI is unavailable."""
from __future__ import annotations

import re
from typing import Any

from app.core.constants import (
    AI_ROUTE_COLLECTIONS_KEYWORDS,
    AI_ROUTE_CUSTOMER_KEYWORDS,
    AI_ROUTE_DASHBOARD_KEYWORDS,
    AI_ROUTE_HELP_KEYWORDS,
    AI_ROUTE_INVOICE_KEYWORDS,
    AI_ROUTE_REMINDER_KEYWORDS,
    AiRoute,
)


def classify_route(message: str) -> dict[str, Any]:
    lower = message.lower().strip()
    if not lower:
        return {"route": AiRoute.CLARIFY, "confidence": 0.3}

    if _matches_any(lower, AI_ROUTE_HELP_KEYWORDS):
        return {"route": AiRoute.HELP, "confidence": 0.95}

    if _matches_any(lower, AI_ROUTE_REMINDER_KEYWORDS):
        return {"route": AiRoute.COLLECTIONS, "confidence": 0.9}

    if _matches_any(lower, AI_ROUTE_INVOICE_KEYWORDS) or re.search(
        r"\b(invoice|bill)\b", lower
    ):
        return {"route": AiRoute.INVOICE, "confidence": 0.88}

    if _matches_any(lower, AI_ROUTE_DASHBOARD_KEYWORDS):
        return {"route": AiRoute.DASHBOARD, "confidence": 0.85}

    if _matches_any(lower, AI_ROUTE_CUSTOMER_KEYWORDS):
        return {"route": AiRoute.CUSTOMER, "confidence": 0.82}

    if _matches_any(lower, AI_ROUTE_COLLECTIONS_KEYWORDS):
        return {"route": AiRoute.COLLECTIONS, "confidence": 0.85}

    return {"route": AiRoute.CLARIFY, "confidence": 0.4}


def _matches_any(text: str, keywords: tuple[str, ...]) -> bool:
    for keyword in keywords:
        if len(keyword) <= 3:
            if re.search(rf"\b{re.escape(keyword)}\b", text):
                return True
        elif keyword in text:
            return True
    return False
