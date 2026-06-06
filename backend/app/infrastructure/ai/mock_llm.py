"""Deterministic LLM stub for local development."""
from __future__ import annotations

import json
import re
from typing import Any

from app.core.constants import AiRoute


class MockLlm:
    async def classify_intent(self, message: str) -> dict[str, Any]:
        lower = message.lower()
        if any(w in lower for w in ("overdue", "reminder", "collect", "payment due")):
            return {"route": AiRoute.COLLECTIONS, "confidence": 0.85}
        if re.search(r"\binvoice\b|\bbill\b|cement|bags", lower):
            return {"route": AiRoute.INVOICE, "confidence": 0.9}
        if any(w in lower for w in ("revenue", "dashboard", "cashflow", "aging")):
            return {"route": AiRoute.DASHBOARD, "confidence": 0.85}
        if any(w in lower for w in ("customer", "trader", "client")):
            return {"route": AiRoute.CUSTOMER, "confidence": 0.8}
        return {"route": AiRoute.CLARIFY, "confidence": 0.5}

    async def extract_entities(self, message: str, intent: str) -> dict[str, Any]:
        entities: dict[str, Any] = {}
        if intent == AiRoute.INVOICE:
            qty_match = re.search(r"(\d+)\s*(bags?|nos|units?)", message, re.I)
            price_match = re.search(r"(?:at|@|₹|rs\.?)\s*(\d+)", message, re.I)
            gst_match = re.search(r"(\d+)%\s*gst", message, re.I)
            name_match = re.search(
                r"(?:invoice|bill)\s+([A-Za-z][A-Za-z\s]+?)(?:\s+for|\s+at|$)",
                message,
                re.I,
            )
            entities = {
                "customer_name": name_match.group(1).strip() if name_match else None,
                "quantity": int(qty_match.group(1)) if qty_match else None,
                "unit": qty_match.group(2).upper() if qty_match else "BAG",
                "unit_price": float(price_match.group(1)) if price_match else None,
                "gst_rate": float(gst_match.group(1)) if gst_match else 18.0,
                "description": "OPC 53 Grade Cement",
            }
        elif intent == AiRoute.CUSTOMER:
            name_match = re.search(r"(?:create|add)\s+customer\s+(.+)", message, re.I)
            entities = {"name": name_match.group(1).strip() if name_match else None}
        return entities

    async def generate_text(self, system: str, user: str) -> str:
        return json.dumps({"message": f"Mock response for: {user[:80]}"})
