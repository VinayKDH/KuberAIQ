"""Clarify agent — helpful fallback when intent is unknown."""
from __future__ import annotations

from app.core.constants import AI_CLARIFY_SUGGESTED_ACTIONS, AI_COMPLIANCE_HINT, AiIntent


async def run_clarify_agent(state: dict) -> dict:
    message = state.get("message", "").lower()

    if any(word in message for word in ("gst", "gstr", "filing", "compliance", "return")):
        return {
            "response": {
                "intent": AiIntent.CLARIFY,
                "message": AI_COMPLIANCE_HINT,
                "requires_confirmation": False,
                "pending_action": None,
                "data": None,
                "suggested_actions": list(AI_CLARIFY_SUGGESTED_ACTIONS),
            }
        }

    if any(word in message for word in ("product", "stock", "catalogue", "catalog", "hsn")):
        return {
            "response": {
                "intent": AiIntent.CLARIFY,
                "message": (
                    "I can help with invoices that use your product catalogue. "
                    "Open Products to add items with HSN and GST, then say "
                    "'create invoice for <customer> with <product>'."
                ),
                "requires_confirmation": False,
                "pending_action": None,
                "data": None,
                "suggested_actions": [
                    {"label": "Create invoice", "value": "Create invoice for a customer"},
                    {"label": "Pending payments", "value": "How much money is pending?"},
                ],
            }
        }

    return {
        "response": {
            "intent": AiIntent.CLARIFY,
            "message": (
                "I'm not sure I understood that. Try one of these, or rephrase with a "
                "customer name, amount, or what you want to check."
            ),
            "requires_confirmation": False,
            "pending_action": None,
            "data": None,
            "suggested_actions": list(AI_CLARIFY_SUGGESTED_ACTIONS),
        }
    }
