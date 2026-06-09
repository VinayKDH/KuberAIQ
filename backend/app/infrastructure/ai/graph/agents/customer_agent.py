"""Customer specialist agent."""
from __future__ import annotations

import uuid

from app.core.constants import AiIntent
from app.infrastructure.ai.mock_llm import MockLlm
from app.infrastructure.ai.tools.executor import ToolExecutor


async def run_customer_agent(state: dict) -> dict:
    llm = state.get("llm") or MockLlm()
    message = state.get("message", "")
    entities = await llm.extract_entities(message, "customer")
    services = state.get("services", {})
    customer_svc = services.get("customer")
    company_id = uuid.UUID(state["company_id"])
    lower = message.lower()

    if any(word in lower for word in ("create", "add", "new")):
        name = entities.get("name")
        phone = entities.get("phone")
        if not name or not phone:
            return {
                "response": {
                    "intent": AiIntent.CLARIFY,
                    "message": "Please provide customer name and 10-digit phone. Example: Add customer Raj Traders 9876543210",
                    "requires_confirmation": False,
                    "pending_action": None,
                    "data": None,
                    "suggested_actions": [],
                }
            }
        preview = {"name": name, "phone": phone}
        if state.get("confirmed"):
            executor = ToolExecutor(services)
            result = await executor.create_customer(company_id, uuid.UUID(state["user_id"]), preview)
            return {
                "response": {
                    "intent": AiIntent.CREATE_CUSTOMER,
                    "message": f"Customer {result['name']} created.",
                    "requires_confirmation": False,
                    "pending_action": None,
                    "data": result,
                    "suggested_actions": [],
                }
            }
        return {
            "response": {
                "intent": AiIntent.CREATE_CUSTOMER,
                "message": f"I'll create customer {name} with phone {phone}. Confirm?",
                "requires_confirmation": True,
                "pending_action": {"type": AiIntent.CREATE_CUSTOMER, "preview": preview},
                "data": None,
                "suggested_actions": [
                    {"label": "Confirm", "value": "confirm"},
                    {"label": "Cancel", "value": "cancel"},
                ],
            }
        }

    name = entities.get("name") or message
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
            "suggested_actions": [
                {"label": f"Create {name}", "value": f"create customer {name}"},
            ],
        }
    }
