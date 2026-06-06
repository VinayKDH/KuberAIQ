"""Assembles and runs the copilot graph (simplified LangGraph-style pipeline)."""
from __future__ import annotations

from typing import Any

from app.core.constants import AiRoute
from app.infrastructure.ai.graph.agents.collections_agent import run_collections_agent
from app.infrastructure.ai.graph.agents.customer_agent import run_customer_agent
from app.infrastructure.ai.graph.agents.dashboard_agent import run_dashboard_agent
from app.infrastructure.ai.graph.agents.invoice_agent import run_invoice_agent
from app.infrastructure.ai.graph.router import route_message
from app.infrastructure.ai.guardrails import validate_response
from app.infrastructure.ai.mock_llm import MockLlm


class CopilotGraph:
    def __init__(self, llm: MockLlm | None = None) -> None:
        self._llm = llm or MockLlm()

    async def run(
        self,
        *,
        company_id: str,
        user_id: str,
        message: str,
        channel: str = "web",
        confirmed: bool = False,
        services: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        state: dict[str, Any] = {
            "company_id": company_id,
            "user_id": user_id,
            "message": message,
            "channel": channel,
            "confirmed": confirmed,
            "services": services or {},
        }
        routed = await route_message(state, self._llm)
        state.update(routed)
        route = state.get("route", AiRoute.CLARIFY)

        if route == AiRoute.INVOICE:
            result = await run_invoice_agent(state)
        elif route == AiRoute.COLLECTIONS:
            result = await run_collections_agent(state)
        elif route == AiRoute.DASHBOARD:
            result = await run_dashboard_agent(state)
        elif route == AiRoute.CUSTOMER:
            result = await run_customer_agent(state)
        else:
            result = {
                "response": {
                    "intent": "clarify",
                    "message": "Could you clarify what you'd like me to do?",
                    "requires_confirmation": False,
                    "pending_action": None,
                    "data": None,
                    "suggested_actions": [],
                }
            }

        response = validate_response(result.get("response", {}))
        response.setdefault("pending_action", None)
        response.setdefault("data", None)
        response.setdefault("suggested_actions", [])
        return response
