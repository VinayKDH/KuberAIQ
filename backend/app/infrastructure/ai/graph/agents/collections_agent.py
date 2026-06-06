"""Collections specialist agent."""
from __future__ import annotations

import uuid

from app.core.constants import AiIntent


async def run_collections_agent(state: dict) -> dict:
    services = state.get("services", {})
    collection = services.get("collection")
    company_id = uuid.UUID(state["company_id"])
    overdue = await collection.list_overdue(company_id)
    total = sum((r["invoice"].amount_due.amount for r in overdue), start=0)
    return {
        "response": {
            "intent": AiIntent.LIST_OVERDUE,
            "message": f"You have {len(overdue)} overdue invoices totalling ₹{total}.",
            "requires_confirmation": False,
            "pending_action": None,
            "data": {
                "count": len(overdue),
                "total": float(total),
                "invoices": [
                    {
                        "invoice_number": r["invoice"].invoice_number,
                        "amount_due": float(r["invoice"].amount_due.amount),
                        "days_overdue": r["days_overdue"],
                    }
                    for r in overdue
                ],
            },
            "suggested_actions": [
                {"label": "Send reminders", "value": "send reminders to all overdue"},
            ],
        }
    }
