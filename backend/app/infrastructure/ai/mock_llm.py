"""Deterministic LLM stub for local development and production fallback."""
from __future__ import annotations

import re
from typing import Any

from app.core.constants import AiRoute
from app.infrastructure.ai.intent_classifier import classify_route


class MockLlm:
    model_name = "mock-llm"

    async def classify_intent(self, message: str) -> dict[str, Any]:
        return classify_route(message)

    async def extract_entities(self, message: str, intent: str) -> dict[str, Any]:
        entities: dict[str, Any] = {}
        if intent in {AiRoute.INVOICE, "invoice"}:
            qty_match = re.search(
                r"(\d+(?:\.\d+)?)\s*(bags?|kg|kgs?|nos|units?|pcs?|liters?|ltr)",
                message,
                re.I,
            )
            price_match = re.search(
                r"(?:at|@|₹|rs\.?|rate)\s*(\d+(?:\.\d+)?)",
                message,
                re.I,
            )
            gst_match = re.search(r"(\d+(?:\.\d+)?)%\s*gst", message, re.I)
            name_match = re.search(
                r"(?:invoice|bill)\s+(?:for\s+)?([A-Za-z][A-Za-z0-9\s.&'-]+?)"
                r"(?:\s+for\s+\d|\s+with\s+|\s+at\s|@|\s+\d+\s*(?:kg|bags?)|$)",
                message,
                re.I,
            )
            for_customer_match = re.search(
                r"\bfor\s+([A-Za-z][A-Za-z0-9\s.&'-]{2,}?)(?:\s+for\s+\d|\s+with\s+|\s+at\s|@|$)",
                message,
                re.I,
            )
            product_match = re.search(
                r"(?:with|of)\s+(\d+(?:\.\d+)?)?\s*(bags?|kg|kgs?|nos|units?|pcs?)?\s*"
                r"([A-Za-z][A-Za-z\s]+?)(?:\s+at\s|@|$)",
                message,
                re.I,
            )
            description = "Item"
            if product_match and product_match.group(3):
                description = product_match.group(3).strip().title()
            elif re.search(r"paneer", message, re.I):
                description = "Paneer"
            elif re.search(r"khoya", message, re.I):
                description = "Khoya"
            elif re.search(r"cement", message, re.I):
                description = "OPC 53 Grade Cement"

            customer_name = None
            if name_match:
                customer_name = name_match.group(1).strip()
            elif for_customer_match:
                customer_name = for_customer_match.group(1).strip()

            entities = {
                "customer_name": customer_name,
                "quantity": float(qty_match.group(1)) if qty_match else None,
                "unit": (qty_match.group(2) if qty_match else "NOS").upper(),
                "unit_price": float(price_match.group(1)) if price_match else None,
                "gst_rate": float(gst_match.group(1)) if gst_match else None,
                "description": description,
            }
        elif intent in {AiRoute.CUSTOMER, "customer"}:
            name_match = re.search(
                r"(?:create|add|new)\s+customer\s+(.+?)(?:\s+\d{10}|$)",
                message,
                re.I,
            )
            find_match = re.search(
                r"(?:find|search|lookup|show)\s+customer\s+(.+)$",
                message,
                re.I,
            )
            phone_match = re.search(r"(\d{10})", message)
            entities = {
                "name": (
                    (name_match.group(1).strip() if name_match else None)
                    or (find_match.group(1).strip() if find_match else None)
                ),
                "phone": phone_match.group(1) if phone_match else None,
            }
        return entities

    async def generate_text(self, system: str, user: str) -> str:
        import json

        return json.dumps({"message": f"Mock response for: {user[:80]}"})
