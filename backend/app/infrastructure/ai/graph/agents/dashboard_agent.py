"""Dashboard specialist agent."""
from __future__ import annotations

import uuid

from app.core.constants import AiIntent
from app.infrastructure.ai.tools.executor import ToolExecutor


async def run_dashboard_agent(state: dict) -> dict:
    services = state.get("services", {})
    company_id = uuid.UUID(state["company_id"])
    executor = ToolExecutor(services)
    summary = await executor.get_dashboard_summary(company_id)
    aging_lines = ", ".join(
        f"{b['bucket']}: ₹{b['outstanding']:,.0f}"
        for b in summary["aging"]
        if b["outstanding"] > 0
    )
    cashflow_total = sum(p["expected_inflow"] for p in summary["cashflow"])
    return {
        "response": {
            "intent": AiIntent.GET_DASHBOARD,
            "message": (
                f"Revenue: ₹{summary['revenue']:,.0f}, "
                f"Pending: ₹{summary['pending']:,.0f}, "
                f"Overdue: ₹{summary['overdue']:,.0f}. "
                f"Expected inflows: ₹{cashflow_total:,.0f}."
                + (f" Aging — {aging_lines}." if aging_lines else "")
            ),
            "requires_confirmation": False,
            "pending_action": None,
            "data": summary,
            "suggested_actions": [],
        }
    }
