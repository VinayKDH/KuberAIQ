"""Intent router node."""
from __future__ import annotations

from app.core.constants import AiRoute
from app.infrastructure.ai.guardrails import filter_injection
from app.infrastructure.ai.mock_llm import MockLlm


async def route_message(state: dict, llm: MockLlm | None = None) -> dict:
    llm = llm or MockLlm()
    message = filter_injection(state.get("message", ""))
    classification = await llm.classify_intent(message)
    route = classification.get("route", AiRoute.CLARIFY)
    return {"route": route, "message": message}
