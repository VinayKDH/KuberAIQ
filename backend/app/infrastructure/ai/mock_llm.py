"""Deterministic LLM stub for local development and production fallback."""
from __future__ import annotations

from typing import Any

from app.core.constants import AiRoute
from app.infrastructure.ai.entity_extractor import (
    extract_customer_entities,
    extract_invoice_entities,
)
from app.infrastructure.ai.intent_classifier import classify_route


class MockLlm:
    model_name = "mock-llm"

    async def classify_intent(self, message: str) -> dict[str, Any]:
        return classify_route(message)

    async def extract_entities(self, message: str, intent: str) -> dict[str, Any]:
        if intent in {AiRoute.INVOICE, "invoice"}:
            return extract_invoice_entities(message)
        if intent in {AiRoute.CUSTOMER, "customer"}:
            return extract_customer_entities(message)
        return {}

    async def generate_text(self, system: str, user: str) -> str:
        import json

        return json.dumps({"message": f"Mock response for: {user[:80]}"})
