"""Invoice specialist agent."""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from app.application.ports.llm import LlmPort
from app.core.constants import AI_CLARIFY_SUGGESTED_ACTIONS, DEFAULT_DUE_DAYS, AiIntent
from app.infrastructure.ai.tools.executor import ToolExecutor


async def run_invoice_agent(state: dict) -> dict:
    llm: LlmPort = state["llm"]
    entities = await llm.extract_entities(state["message"], "invoice")
    services = state.get("services", {})
    executor = ToolExecutor(services)
    company_id = uuid.UUID(state["company_id"])

    customer_name = entities.get("customer_name")
    if not customer_name:
        return {
            "response": {
                "intent": AiIntent.CLARIFY,
                "message": (
                    "Which customer should I invoice? "
                    "Example: Invoice Manu Paneer for 10 kg paneer at 200"
                ),
                "requires_confirmation": False,
                "pending_action": None,
                "data": None,
                "suggested_actions": list(AI_CLARIFY_SUGGESTED_ACTIONS),
            }
        }

    customers = await executor.find_customer(company_id, customer_name)
    if not customers:
        return {
            "response": {
                "intent": AiIntent.CLARIFY,
                "message": f"I couldn't find '{customer_name}'. Create the customer first?",
                "requires_confirmation": False,
                "pending_action": None,
                "data": None,
                "suggested_actions": [
                    {
                        "label": f"Add {customer_name}",
                        "value": f"Add customer {customer_name} 9000000000",
                    },
                    {"label": "Find customers", "value": f"find customer {customer_name}"},
                ],
            }
        }
    customer = customers[0]
    qty = entities.get("quantity") or 1
    price = entities.get("unit_price") or 0
    product = await executor.find_product(company_id, entities.get("description", ""))
    gst_rate = entities.get("gst_rate") or (float(product.gst_rate) if product else 18)
    hsn_sac = product.hsn_sac if product else None
    unit = entities.get("unit") or (product.unit if product else "NOS")
    description = product.name if product else entities.get("description", "Item")
    today = date.today()
    preview = {
        "customer_id": str(customer.id),
        "customer_name": customer.name,
        "issue_date": today,
        "due_date": today + timedelta(days=DEFAULT_DUE_DAYS),
        "status": "ISSUED",
        "items": [
            {
                "description": description,
                "quantity": Decimal(str(qty)),
                "unit_price": Decimal(str(price or (product.default_price if product else 0))),
                "gst_rate": Decimal(str(gst_rate)),
                "hsn_sac": hsn_sac,
                "unit": unit,
                "product_id": str(product.id) if product else None,
            }
        ],
    }
    if state.get("confirmed"):
        result = await executor.create_invoice(company_id, uuid.UUID(state["user_id"]), preview)
        return {
            "response": {
                "intent": AiIntent.CREATE_INVOICE,
                "message": f"Invoice {result.get('invoice_number')} created.",
                "requires_confirmation": False,
                "pending_action": None,
                "data": result,
                "suggested_actions": [],
            }
        }
    return {
        "response": {
            "intent": AiIntent.CREATE_INVOICE,
            "message": (
                f"I'll create an invoice for {customer.name} — {qty} @ ₹{price}, "
                f"{gst_rate}% GST. Confirm?"
            ),
            "requires_confirmation": True,
            "pending_action": {"type": AiIntent.CREATE_INVOICE, "preview": preview},
            "data": None,
            "suggested_actions": [
                {"label": "Confirm", "value": "confirm"},
                {"label": "Cancel", "value": "cancel"},
            ],
        }
    }
