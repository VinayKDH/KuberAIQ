"""Help / onboarding agent — guides users on what the copilot can do."""
from __future__ import annotations

from app.core.constants import AI_HELP_SUGGESTED_ACTIONS, AiIntent


async def run_help_agent(_state: dict) -> dict:
    return {
        "response": {
            "intent": AiIntent.CLARIFY,
            "message": (
                "I can help you with invoices, collections, customers, and business summaries. "
                "Try asking about pending payments, overdue invoices, or say "
                "'create invoice for <customer>'."
            ),
            "requires_confirmation": False,
            "pending_action": None,
            "data": None,
            "suggested_actions": list(AI_HELP_SUGGESTED_ACTIONS),
        }
    }
