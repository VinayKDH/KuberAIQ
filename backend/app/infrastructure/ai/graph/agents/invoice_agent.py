"""Invoice specialist agent."""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from app.core.constants import DEFAULT_DUE_DAYS, AiIntent
from app.infrastructure.ai.mock_llm import MockLlm
from app.infrastructure.ai.tools.executor import ToolExecutor


async def run_invoice_agent(state: dict) -> dict:
    llm = MockLlm()
    entities = await llm.extract_entities(state["message"], "invoice")
    services = state.get("services", {})
    executor = ToolExecutor(services)
    company_id = uuid.UUID(state["company_id"])

    customer_name = entities.get("customer_name")
    if not customer_name:
        return {
            "response": {
                "intent": AiIntent.CLARIFY,
                "message": "Which customer should I invoice?",
                "requires_confirmation": False,
                "pending_action": None,
                "data": None,
                "suggested_actions": [],
            }
        }

    customers = await executor.find_customer(company_id, customer_name)
    if not customers:
        return {
            "response": {
                "intent": AiIntent.CLARIFY,
                "message": f"I couldn't find '{customer_name}'. Create them first?",
                "requires_confirmation": False,
                "pending_action": None,
                "data": None,
                "suggested_actions": [],
            }
        }
    customer = customers[0]
    qty = entities.get("quantity") or 1
    price = entities.get("unit_price") or 0
    gst_rate = entities.get("gst_rate") or 18
    today = date.today()
    preview = {
        "customer_id": str(customer.id),
        "customer_name": customer.name,
        "issue_date": today,
        "due_date": today + timedelta(days=DEFAULT_DUE_DAYS),
        "status": "ISSUED",
        "items": [
            {
                "description": entities.get("description", "Item"),
                "quantity": Decimal(str(qty)),
                "unit_price": Decimal(str(price)),
                "gst_rate": Decimal(str(gst_rate)),
                "unit": entities.get("unit", "NOS"),
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
                {"label": "Confirm", "value": "yes"},
                {"label": "Cancel", "value": "no"},
            ],
        }
    }
