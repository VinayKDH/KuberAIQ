"""Intent router node."""
from __future__ import annotations

from app.application.ports.llm import LlmPort
from app.core.constants import AiAwaiting, AiRoute
from app.infrastructure.ai.entity_extractor import extract_phone_from_text, parse_customer_details_from_text
from app.infrastructure.ai.guardrails import filter_injection
from app.infrastructure.ai.mock_llm import MockLlm


async def route_message(state: dict, llm: LlmPort | None = None) -> dict:
    llm = llm or state.get("llm")
    message = filter_injection(state.get("message", ""))
    lower = message.strip().lower()
    context = state.get("conversation_context") or {}
    awaiting = context.get("awaiting")

    clarify = state.get("clarify_pending") or {}
    if clarify.get("awaiting") == AiAwaiting.CREATE_MISSING_CUSTOMER:
        inner = clarify.get("context") or {}
        if inner.get("invoice_draft") and extract_phone_from_text(message):
            return {"route": AiRoute.INVOICE, "message": message}
    if awaiting in {
        AiAwaiting.CUSTOMER_NAME,
        AiAwaiting.CUSTOMER_PHONE,
        AiAwaiting.CREATE_MISSING_CUSTOMER,
    }:
        return {"route": AiRoute.CUSTOMER, "message": message}
    if awaiting == AiAwaiting.INVOICE_CUSTOMER:
        return {"route": AiRoute.INVOICE, "message": message}
    if lower.startswith(("add customer", "create customer", "new customer")):
        return {"route": AiRoute.CUSTOMER, "message": message}
    if lower.startswith(("create invoice", "make invoice", "invoice ", "bill ")):
        return {"route": AiRoute.INVOICE, "message": message}
    details = parse_customer_details_from_text(message)
    if details.get("phone") and context.get("awaiting_name") and not details.get("name"):
        return {"route": AiRoute.CUSTOMER, "message": message}

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
