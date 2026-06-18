"""Conversation memory — resolves follow-ups and multi-turn clarify flows."""
from __future__ import annotations

import re
from typing import Any

from app.core.constants import (
    AI_CONTEXT_CANCEL_WORDS,
    AI_CONTEXT_CONFIRM_WORDS,
    AI_CONTEXT_CREATE_CUSTOMER_AFFIRMATIONS,
    AI_CONTEXT_INVOICE_FOLLOW_UPS,
    AI_CONTEXT_PRONOUN_PHRASES,
    AI_CONTEXT_REMINDER_FOLLOW_UPS,
    AiAwaiting,
    AiIntent,
)

from app.infrastructure.ai.entity_extractor import (
    extract_customer_entities,
    extract_phone_from_text,
    parse_customer_details_from_text,
)


def _extract_phone(text: str) -> str | None:
    return extract_phone_from_text(text)


def _is_phone_only(text: str) -> bool:
    digits = re.sub(r"\D", "", text)
    return len(digits) == 10 and digits == text.replace(" ", "")


def _is_likely_customer_name(text: str) -> bool:
    stripped = text.strip()
    lower = stripped.lower()
    if not stripped or len(stripped) < 2 or len(stripped) > 80:
        return False
    if lower in AI_CONTEXT_CONFIRM_WORDS or lower in AI_CONTEXT_CANCEL_WORDS:
        return False
    if _is_phone_only(stripped) or _extract_phone(stripped):
        return False
    if stripped.isdigit():
        return False
    if any(ch in stripped for ch in ("?", "!", "@", "₹")):
        return False
    word_count = len(stripped.split())
    if word_count > 8:
        return False
    return bool(re.search(r"[A-Za-z]", stripped))


def build_conversation_context(
    turns: list[dict[str, Any]],
    clarify_pending: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive slots from session history and any in-flight clarify state."""
    ctx: dict[str, Any] = {
        "last_customer_name": None,
        "last_customers": [],
        "last_invoices": [],
        "missing_customer": None,
        "last_invoice_request": None,
        "last_intent": None,
        "last_assistant_message": None,
        "last_user_message": None,
        "awaiting": None,
        "awaiting_phone": None,
        "awaiting_name": None,
        "original_invoice_message": None,
        "invoice_draft": None,
    }

    if clarify_pending and clarify_pending.get("type") == AiIntent.CLARIFY:
        inner = clarify_pending.get("context") or {}
        ctx["awaiting"] = clarify_pending.get("awaiting")
        ctx["awaiting_phone"] = inner.get("phone")
        ctx["awaiting_name"] = inner.get("name")
        ctx["missing_customer"] = inner.get("missing_customer")
        ctx["original_invoice_message"] = inner.get("original_invoice_message")
        ctx["invoice_draft"] = inner.get("invoice_draft")

    for turn in reversed(turns):
        assistant = turn.get("assistant") or {}
        user = turn.get("user") or ""
        intent = assistant.get("intent", "")
        data = assistant.get("data") or {}
        message = assistant.get("message") or ""

        if ctx["last_user_message"] is None and user:
            ctx["last_user_message"] = user
        if ctx["last_intent"] is None and intent:
            ctx["last_intent"] = intent
        if ctx["last_assistant_message"] is None and message:
            ctx["last_assistant_message"] = message

        if data.get("missing_customer") and not ctx["missing_customer"]:
            ctx["missing_customer"] = data["missing_customer"]
        if data.get("original_invoice_message") and not ctx["original_invoice_message"]:
            ctx["original_invoice_message"] = data["original_invoice_message"]

        customers = data.get("customers")
        if customers and isinstance(customers, list) and not ctx["last_customers"]:
            ctx["last_customers"] = customers
            if customers[0].get("name"):
                ctx["last_customer_name"] = customers[0]["name"]

        invoices = data.get("invoices")
        if invoices and isinstance(invoices, list) and not ctx["last_invoices"]:
            ctx["last_invoices"] = invoices
            if invoices[0].get("customer_name") and not ctx["last_customer_name"]:
                ctx["last_customer_name"] = invoices[0]["customer_name"]

        preview = (assistant.get("pending_action") or {}).get("preview") or {}
        if preview.get("customer_name") and not ctx["last_customer_name"]:
            ctx["last_customer_name"] = preview["customer_name"]

        if intent == AiIntent.CREATE_INVOICE and user and not ctx["last_invoice_request"]:
            ctx["last_invoice_request"] = user

        lower_user = user.lower()
        if ("create customer" in lower_user or "add customer" in lower_user) and not ctx.get(
            "awaiting_name"
        ):
            partial = extract_customer_entities(user)
            if partial.get("name") and not partial.get("phone"):
                ctx["awaiting_name"] = partial["name"]

        if ctx["last_customer_name"] and ctx["last_intent"] and ctx["last_assistant_message"]:
            break

    return ctx


def resolve_message_with_context(message: str, context: dict[str, Any]) -> str:
    """Rewrite short or ambiguous follow-ups into actionable commands."""
    stripped = message.strip()
    if not stripped:
        return message

    lower = stripped.lower()
    awaiting = context.get("awaiting")

    labeled = parse_customer_details_from_text(stripped)
    if (
        labeled.get("name")
        and labeled.get("phone")
        and not re.search(r"\b(invoice|bill)\b", lower)
    ):
        return f"Add customer {labeled['name']} {labeled['phone']}"

    if awaiting == AiAwaiting.CUSTOMER_NAME and context.get("awaiting_phone"):
        if _is_likely_customer_name(stripped):
            return f"Add customer {stripped} {context['awaiting_phone']}"

    if awaiting == AiAwaiting.CUSTOMER_PHONE and context.get("awaiting_name"):
        phone = _extract_phone(stripped)
        if phone:
            return f"Add customer {context['awaiting_name']} {phone}"

    if awaiting == AiAwaiting.CREATE_MISSING_CUSTOMER:
        missing = context.get("missing_customer")
        phone = extract_phone_from_text(stripped)
        if missing and phone and context.get("invoice_draft"):
            return stripped
        if missing and phone:
            return f"Add customer {missing} {phone}"
        if missing and any(phrase in lower for phrase in AI_CONTEXT_CREATE_CUSTOMER_AFFIRMATIONS):
            return f"Add customer {missing}"

    if awaiting == AiAwaiting.INVOICE_CUSTOMER and _is_likely_customer_name(stripped):
        return f"Create invoice for {stripped}"

    if context.get("last_intent") == AiIntent.CLARIFY:
        assistant_msg = (context.get("last_assistant_message") or "").lower()
        if "which customer" in assistant_msg and _is_likely_customer_name(stripped):
            return f"Create invoice for {stripped}"
        if "customer or business name" in assistant_msg and context.get("awaiting_phone"):
            if _is_likely_customer_name(stripped):
                return f"Add customer {stripped} {context['awaiting_phone']}"
        if (
            "10-digit phone" in assistant_msg
            or "name and 10-digit phone" in assistant_msg
            or "customer name and" in assistant_msg
        ):
            partial_name = context.get("awaiting_name")
            if labeled.get("phone") and partial_name and not labeled.get("name"):
                return f"Add customer {partial_name} {labeled['phone']}"
        if "phone" in assistant_msg and context.get("missing_customer"):
            phone = _extract_phone(stripped)
            if phone:
                return f"Add customer {context['missing_customer']} {phone}"

    missing = context.get("missing_customer")
    original = context.get("original_invoice_message")
    if missing and original and _is_likely_customer_name(stripped) and stripped.upper() == missing.upper():
        phone = _extract_phone(stripped)
        if not phone:
            return f"find customer {missing}"

    if any(phrase in lower for phrase in AI_CONTEXT_REMINDER_FOLLOW_UPS):
        if context.get("last_intent") in {AiIntent.LIST_OVERDUE, AiIntent.LIST_UNPAID}:
            return "send reminders to all overdue"
        customer = context.get("last_customer_name")
        if customer:
            return f"send reminder for {customer}"

    if any(phrase in lower for phrase in AI_CONTEXT_INVOICE_FOLLOW_UPS):
        customer = context.get("last_customer_name")
        if customer:
            return f"create invoice for {customer}"

    if any(phrase in lower for phrase in AI_CONTEXT_PRONOUN_PHRASES):
        customer = context.get("last_customer_name")
        if customer and ("invoice" in lower or "bill" in lower):
            return f"create invoice for {customer}"
        if customer and "remind" in lower:
            return f"send reminder for {customer}"

    customers = context.get("last_customers") or []
    if customers and isinstance(customers, list) and customers:
        name = customers[0].get("name")
        if name and ("invoice" in lower or "bill" in lower):
            return f"create invoice for {name}"

    invoices = context.get("last_invoices") or []
    if invoices and isinstance(invoices, list) and invoices:
        customer_name = invoices[0].get("customer_name")
        if customer_name and "remind" in lower:
            return f"send reminder for {customer_name}"

    return message


def augment_message_with_history(
    message: str,
    turns: list[dict[str, Any]],
    clarify_pending: dict[str, Any] | None = None,
) -> str:
    context = build_conversation_context(turns, clarify_pending)
    return resolve_message_with_context(message, context)


def build_clarify_pending(
    *,
    awaiting: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": AiIntent.CLARIFY,
        "awaiting": awaiting,
        "context": context,
    }


def is_confirmable_pending(pending_action: dict[str, Any] | None) -> bool:
    if not pending_action:
        return False
    return pending_action.get("type") != AiIntent.CLARIFY
