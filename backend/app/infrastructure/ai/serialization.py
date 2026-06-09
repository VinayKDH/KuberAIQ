"""JSON-safe serialization for AI chat payloads."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any


def serialize_chat_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: serialize_chat_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serialize_chat_value(item) for item in value]
    return value


def serialize_chat_response(response: dict[str, Any]) -> dict[str, Any]:
    return serialize_chat_value(response)
