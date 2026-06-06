"""Customer specialist agent."""
from __future__ import annotations

import uuid

from app.core.constants import AiIntent
from app.infrastructure.ai.mock_llm import MockLlm


async def run_customer_agent(state: dict) -> dict:
    llm = MockLlm()
    entities = await llm.extract_entities(state["message"], "customer")
    services = state.get("services", {})
    customer_svc = services.get("customer")
    company_id = uuid.UUID(state["company_id"])
    name = entities.get("name") or state["message"]
    customers, _ = await customer_svc.search(company_id, name, 1, 5)
    if customers:
        return {
            "response": {
                "intent": AiIntent.FIND_CUSTOMER,
                "message": f"Found {len(customers)} customer(s) matching '{name}'.",
                "requires_confirmation": False,
                "pending_action": None,
                "data": {
                    "customers": [
                        {"id": str(c.id), "name": c.name, "phone": c.phone.value}
                        for c in customers
                    ]
                },
                "suggested_actions": [],
            }
        }
    return {
        "response": {
            "intent": AiIntent.CLARIFY,
            "message": f"No customer found for '{name}'. Would you like to create one?",
            "requires_confirmation": False,
            "pending_action": None,
            "data": None,
            "suggested_actions": [],
        }
    }
