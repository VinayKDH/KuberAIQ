"""Session context augmentation tests."""
from __future__ import annotations

from app.infrastructure.ai.session_context import augment_message_with_history


def test_follow_up_reminder_after_unpaid_list() -> None:
    turns = [
        {
            "user": "pending?",
            "assistant": {"intent": "list_unpaid", "data": {"invoices": [{"customer_name": "ABC"}]}},
        }
    ]
    result = augment_message_with_history("send reminder to them", turns)
    assert result == "send reminders to all overdue"
