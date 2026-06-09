"""Short-term session memory — rewrites follow-up messages using recent turns."""
from __future__ import annotations

from typing import Any

_FOLLOW_UP_PHRASES = (
    "them",
    "that customer",
    "same customer",
    "send it",
    "remind them",
    "for him",
    "for her",
    "do it",
    "go ahead with that",
)

_REMINDER_FOLLOW_UPS = ("send reminder", "remind them", "send it", "whatsapp them")


def augment_message_with_history(message: str, turns: list[dict[str, Any]]) -> str:
    if not turns:
        return message

    lower = message.strip().lower()
    if not any(phrase in lower for phrase in _FOLLOW_UP_PHRASES):
        return message

    last_assistant = turns[-1].get("assistant", {})
    intent = last_assistant.get("intent", "")
    data = last_assistant.get("data") or {}

    if any(phrase in lower for phrase in _REMINDER_FOLLOW_UPS):
        if intent in {"list_overdue", "list_unpaid"}:
            return "send reminders to all overdue"

    customers = data.get("customers")
    if customers and isinstance(customers, list) and customers:
        name = customers[0].get("name")
        if name and ("invoice" in lower or "bill" in lower):
            return f"create invoice for {name}"

    invoices = data.get("invoices")
    if invoices and isinstance(invoices, list) and invoices:
        customer_name = invoices[0].get("customer_name")
        if customer_name and "remind" in lower:
            return f"send reminder for {customer_name}"

    return message
