"""Dashboard specialist agent."""
from __future__ import annotations

import uuid
from datetime import date

from app.core.constants import AiIntent


async def run_dashboard_agent(state: dict) -> dict:
    services = state.get("services", {})
    dashboard = services.get("dashboard")
    company_id = uuid.UUID(state["company_id"])
    today = date.today()
    from_date = date(today.year, 4, 1) if today.month >= 4 else date(today.year - 1, 4, 1)
    summary = await dashboard.summary(company_id, from_date, today)
    return {
        "response": {
            "intent": AiIntent.GET_DASHBOARD,
            "message": (
                f"Revenue: ₹{summary['revenue']:,.0f}, "
                f"Pending: ₹{summary['pending']:,.0f}, "
                f"Overdue: ₹{summary['overdue']:,.0f}."
            ),
            "requires_confirmation": False,
            "pending_action": None,
            "data": summary,
            "suggested_actions": [],
        }
    }
