"""Intent router node."""
from __future__ import annotations

from app.application.ports.llm import LlmPort
from app.core.constants import AiRoute
from app.infrastructure.ai.guardrails import filter_injection
from app.infrastructure.ai.mock_llm import MockLlm


async def route_message(state: dict, llm: LlmPort | None = None) -> dict:
    llm = llm or state.get("llm")
    message = filter_injection(state.get("message", ""))
    if llm is None:
        llm = MockLlm()
        classification = await llm.classify_intent(message)
        route = classification.get("route", AiRoute.CLARIFY)
        if message.strip().lower() in {"hello", "hello there", "hi"}:
            route = AiRoute.CLARIFY
        return {"route": route, "message": message}
    classification = await llm.classify_intent(message)
    route = classification.get("route", AiRoute.CLARIFY)
    return {"route": route, "message": message}
