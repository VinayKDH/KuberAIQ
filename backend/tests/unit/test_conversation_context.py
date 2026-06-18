"""Conversation context resolution tests."""
from __future__ import annotations

from app.core.constants import AiAwaiting, AiIntent
from app.infrastructure.ai.conversation_context import (
    augment_message_with_history,
    build_clarify_pending,
    build_conversation_context,
    is_confirmable_pending,
    resolve_message_with_context,
)


def test_follow_up_reminder_after_unpaid_list() -> None:
    turns = [
        {
            "user": "pending?",
            "assistant": {"intent": "list_unpaid", "data": {"invoices": [{"customer_name": "ABC"}]}},
        }
    ]
    result = augment_message_with_history("send reminder to them", turns)
    assert result == "send reminders to all overdue"


def test_phone_then_name_follow_up() -> None:
    clarify = build_clarify_pending(
        awaiting=AiAwaiting.CUSTOMER_NAME,
        context={"phone": "9000000000"},
    )
    result = augment_message_with_history("Raj Traders", [], clarify)
    assert result == "Add customer Raj Traders 9000000000"


def test_missing_customer_phone_follow_up() -> None:
    clarify = build_clarify_pending(
        awaiting=AiAwaiting.CREATE_MISSING_CUSTOMER,
        context={
            "missing_customer": "AIMLGYAN",
            "original_invoice_message": "Create invoice for AIMLGYAN",
        },
    )
    result = augment_message_with_history("9876501234", [], clarify)
    assert result == "Add customer AIMLGYAN 9876501234"


def test_invoice_customer_name_follow_up() -> None:
    clarify = build_clarify_pending(awaiting=AiAwaiting.INVOICE_CUSTOMER, context={})
    result = augment_message_with_history("AIMLGYAN", [], clarify)
    assert result == "Create invoice for AIMLGYAN"


def test_which_customer_clarify_from_history() -> None:
    turns = [
        {
            "user": "create invoice",
            "assistant": {
                "intent": AiIntent.CLARIFY,
                "message": "Which customer should I invoice?",
            },
        }
    ]
    result = augment_message_with_history("AIMLGYAN", turns)
    assert result == "Create invoice for AIMLGYAN"


def test_pronoun_invoice_after_customer_list() -> None:
    turns = [
        {
            "user": "find customer raj",
            "assistant": {
                "intent": AiIntent.FIND_CUSTOMER,
                "data": {"customers": [{"name": "Raj Traders", "id": "1"}]},
            },
        }
    ]
    result = augment_message_with_history("invoice them", turns)
    assert result == "create invoice for Raj Traders"


def test_labeled_name_phone_from_history_clarify() -> None:
    turns = [
        {
            "user": "create customer kamal joshi",
            "assistant": {
                "intent": "clarify",
                "message": "Please provide customer name and 10-digit phone.",
            },
        }
    ]
    result = augment_message_with_history("Name Kamal Joshi. Phone 9258843443", turns)
    assert result == "Add customer Kamal Joshi 9258843443"


def test_name_then_phone_follow_up_with_pending() -> None:
    clarify = build_clarify_pending(
        awaiting=AiAwaiting.CUSTOMER_PHONE,
        context={"name": "kamal joshi"},
    )
    result = augment_message_with_history("9258843443", [], clarify)
    assert result == "Add customer kamal joshi 9258843443"


def test_clarify_pending_not_confirmable() -> None:
    pending = build_clarify_pending(
        awaiting=AiAwaiting.CUSTOMER_NAME,
        context={"phone": "9000000000"},
    )
    assert is_confirmable_pending(pending) is False


def test_build_context_from_missing_customer_data() -> None:
    turns = [
        {
            "user": "invoice for XYZ",
            "assistant": {
                "intent": AiIntent.CLARIFY,
                "data": {
                    "missing_customer": "XYZ",
                    "original_invoice_message": "invoice for XYZ",
                },
            },
        }
    ]
    ctx = build_conversation_context(turns)
    assert ctx["missing_customer"] == "XYZ"
    assert ctx["original_invoice_message"] == "invoice for XYZ"


def test_resolve_uses_last_customer_for_invoice_them() -> None:
    ctx = {"last_customer_name": "Manu Paneer", "last_intent": AiIntent.FIND_CUSTOMER}
    assert resolve_message_with_context("bill them", ctx) == "create invoice for Manu Paneer"
