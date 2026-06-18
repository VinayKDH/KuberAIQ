"""Customer specialist agent."""
from __future__ import annotations

import uuid

from app.application.ports.llm import LlmPort
from app.core.constants import AiAwaiting, AiIntent
from app.infrastructure.ai.conversation_context import build_clarify_pending
from app.infrastructure.ai.tools.executor import ToolExecutor


async def run_customer_agent(state: dict) -> dict:
    llm: LlmPort = state["llm"]
    message = state.get("message", "")
    entities = await llm.extract_entities(message, "customer")
    services = state.get("services", {})
    customer_svc = services.get("customer")
    company_id = uuid.UUID(state["company_id"])
    lower = message.lower()

    if any(word in lower for word in ("create", "add", "new")):
        name = entities.get("name")
        phone = entities.get("phone")
        if phone and not name:
            clarify = build_clarify_pending(
                awaiting=AiAwaiting.CUSTOMER_NAME,
                context={"phone": phone},
            )
            return {
                "response": {
                    "intent": AiIntent.CLARIFY,
                    "message": (
                        f"I have phone {phone}. What is the customer or business name? "
                        "Example: Add customer Raj Traders 9876543210"
                    ),
                    "requires_confirmation": False,
                    "pending_action": clarify,
                    "data": {"awaiting_phone": phone},
                    "suggested_actions": [
                        {
                            "label": f"Use Customer {phone[-4:]}",
                            "value": f"Add customer Customer {phone[-4:]} {phone}",
                        },
                    ],
                }
            }
        if name and not phone:
            clarify = build_clarify_pending(
                awaiting=AiAwaiting.CUSTOMER_PHONE,
                context={"name": name},
            )
            return {
                "response": {
                    "intent": AiIntent.CLARIFY,
                    "message": (
                        f"I have name {name}. What is their 10-digit mobile number? "
                        "Example: 9876543210 or Name Kamal Joshi. Phone 9876543210"
                    ),
                    "requires_confirmation": False,
                    "pending_action": clarify,
                    "data": {"awaiting_name": name},
                    "suggested_actions": [],
                }
            }
        if not name or not phone:
            clarify = build_clarify_pending(
                awaiting=AiAwaiting.CUSTOMER_NAME,
                context={},
            )
            return {
                "response": {
                    "intent": AiIntent.CLARIFY,
                    "message": (
                        "Please provide customer name and 10-digit phone. "
                        "Example: Add customer Raj Traders 9876543210"
                    ),
                    "requires_confirmation": False,
                    "pending_action": clarify,
                    "data": None,
                    "suggested_actions": [],
                }
            }
        preview = {"name": name, "phone": phone}
        if state.get("confirmed"):
            executor = ToolExecutor(services)
            result = await executor.create_customer(company_id, uuid.UUID(state["user_id"]), preview)
            ctx = state.get("conversation_context") or {}
            original_invoice = ctx.get("original_invoice_message")
            message = f"Customer {result['name']} created."
            suggested: list[dict[str, str]] = []
            if original_invoice:
                message += f" You can now continue with your invoice."
                suggested.append(
                    {
                        "label": f"Invoice {result['name']}",
                        "value": original_invoice,
                    }
                )
            return {
                "response": {
                    "intent": AiIntent.CREATE_CUSTOMER,
                    "message": message,
                    "requires_confirmation": False,
                    "pending_action": None,
                    "data": result,
                    "suggested_actions": suggested,
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
