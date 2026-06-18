"""Assembles and runs the copilot graph (simplified LangGraph-style pipeline)."""
from __future__ import annotations

from typing import Any

from app.core.constants import AiRoute
from app.infrastructure.ai.graph.agents.collections_agent import run_collections_agent
from app.infrastructure.ai.graph.agents.customer_agent import run_customer_agent
from app.infrastructure.ai.graph.agents.dashboard_agent import run_dashboard_agent
from app.infrastructure.ai.graph.agents.clarify_agent import run_clarify_agent
from app.infrastructure.ai.graph.agents.help_agent import run_help_agent
from app.infrastructure.ai.graph.agents.invoice_agent import run_invoice_agent
from app.infrastructure.ai.conversation_context import (
    augment_message_with_history,
    build_conversation_context,
    is_confirmable_pending,
)
from app.infrastructure.ai.serialization import serialize_chat_response
from app.infrastructure.ai.graph.router import route_message
from app.infrastructure.ai.guardrails import validate_response
from app.application.ports.llm import LlmPort
from app.infrastructure.ai.mock_llm import MockLlm


class CopilotGraph:
    def __init__(self, llm: LlmPort | None = None) -> None:
        self._llm = llm or MockLlm()
        self.model_name = getattr(self._llm, "model_name", self._llm.__class__.__name__)

    async def run(
        self,
        *,
        company_id: str,
        user_id: str,
        message: str,
        channel: str = "web",
        confirmed: bool = False,
        services: dict[str, Any] | None = None,
        history: list[dict[str, Any]] | None = None,
        clarify_pending: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        history = history or []
        conversation_context = build_conversation_context(history, clarify_pending)
        resolved_message = augment_message_with_history(message, history, clarify_pending)
        state: dict[str, Any] = {
            "company_id": company_id,
            "user_id": user_id,
            "message": resolved_message,
            "original_message": message,
            "channel": channel,
            "confirmed": confirmed,
            "services": services or {},
            "llm": self._llm,
            "history": history,
            "conversation_context": conversation_context,
            "clarify_pending": clarify_pending,
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
        elif route == AiRoute.HELP:
            result = await run_help_agent(state)
        else:
            result = await run_clarify_agent(state)

        response = validate_response(result.get("response", {}))
        response["route"] = route
        response.setdefault("pending_action", None)
        response.setdefault("data", None)
        response.setdefault("suggested_actions", [])
        return serialize_chat_response(response)
