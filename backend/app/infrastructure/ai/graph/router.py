"""Intent router node."""
from __future__ import annotations

from app.application.ports.llm import LlmPort
from app.core.constants import AiRoute
from app.infrastructure.ai.guardrails import filter_injection


async def route_message(state: dict, llm: LlmPort | None = None) -> dict:
    llm = llm or state.get("llm")
    if llm is None:
        raise ValueError("Copilot graph requires an LLM in state")
    message = filter_injection(state.get("message", ""))
    classification = await llm.classify_intent(message)
    route = classification.get("route", AiRoute.CLARIFY)
    return {"route": route, "message": message}
