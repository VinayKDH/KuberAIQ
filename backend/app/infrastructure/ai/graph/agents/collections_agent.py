"""Collections specialist agent."""
from __future__ import annotations

import uuid

from app.core.constants import AiIntent
from app.infrastructure.ai.tools.executor import ToolExecutor


def _invoice_rows(rows: list[dict]) -> list[dict]:
    return [
        {
            "invoice_number": r["invoice"].invoice_number,
            "customer_name": r["customer_name"],
            "amount_due": float(r["invoice"].amount_due.amount),
            "days_overdue": r["days_overdue"],
            "due_date": r["invoice"].due_date.isoformat(),
            "is_overdue": r.get("is_overdue", r["days_overdue"] > 0),
        }
        for r in rows
    ]


async def run_collections_agent(state: dict) -> dict:
    services = state.get("services", {})
    collection = services.get("collection")
    if collection is None:
        return {
            "response": {
                "intent": AiIntent.CLARIFY,
                "message": "Collections service is unavailable right now. Please try again shortly.",
                "requires_confirmation": False,
                "pending_action": None,
                "data": None,
                "suggested_actions": [],
            }
        }

    company_id = uuid.UUID(state["company_id"])
    user_id = uuid.UUID(state["user_id"])
    executor = ToolExecutor(services)
    message = state.get("message", "").lower()

    if any(
        phrase in message
        for phrase in ("send reminder", "remind all", "bulk remind", "reminders to all")
    ):
        preview = await executor.bulk_reminder_preview(company_id)
        if preview["count"] == 0:
            return {
                "response": {
                    "intent": AiIntent.LIST_OVERDUE,
                    "message": "You have no overdue invoices to remind.",
                    "requires_confirmation": False,
                    "pending_action": None,
                    "data": preview,
                    "suggested_actions": [],
                }
            }
        if state.get("confirmed"):
            sent = await executor.bulk_send_reminders(company_id, user_id)
            return {
                "response": {
                    "intent": AiIntent.BULK_SEND_REMINDERS,
                    "message": f"Sent {len(sent)} WhatsApp reminders.",
                    "requires_confirmation": False,
                    "pending_action": None,
                    "data": {"sent_count": len(sent)},
                    "suggested_actions": [],
                }
            }
        return {
            "response": {
                "intent": AiIntent.BULK_SEND_REMINDERS,
                "message": (
                    f"Send reminders to {preview['count']} overdue invoices "
                    f"totalling ₹{preview['total_outstanding']:,.0f}?"
                ),
                "requires_confirmation": True,
                "pending_action": {
                    "type": AiIntent.BULK_SEND_REMINDERS,
                    "preview": preview,
                },
                "data": None,
                "suggested_actions": [
                    {"label": "Confirm", "value": "confirm"},
                    {"label": "Cancel", "value": "cancel"},
                ],
            }
        }

    wants_overdue_only = any(
        word in message for word in ("overdue", "late", "past due", "delayed")
    )
    if wants_overdue_only:
        overdue = await collection.list_overdue(company_id)
        total = sum((r["invoice"].amount_due.amount for r in overdue), start=0)
        return {
            "response": {
                "intent": AiIntent.LIST_OVERDUE,
                "message": f"You have {len(overdue)} overdue invoices totalling ₹{total:,.0f}.",
                "requires_confirmation": False,
                "pending_action": None,
                "data": {
                    "count": len(overdue),
                    "total": float(total),
                    "invoices": _invoice_rows(overdue),
                },
                "suggested_actions": [
                    {"label": "Send reminders", "value": "send reminders to all overdue"},
                ],
            }
        }

    unpaid = await collection.list_unpaid(company_id)
    total = sum((r["invoice"].amount_due.amount for r in unpaid), start=0)
    overdue_count = sum(1 for r in unpaid if r.get("is_overdue"))
    return {
        "response": {
            "intent": AiIntent.LIST_UNPAID,
            "message": (
                f"You have {len(unpaid)} unpaid invoices totalling ₹{total:,.0f}"
                + (f" ({overdue_count} overdue)." if overdue_count else ".")
            ),
            "requires_confirmation": False,
            "pending_action": None,
            "data": {
                "count": len(unpaid),
                "total": float(total),
                "overdue_count": overdue_count,
                "invoices": _invoice_rows(unpaid),
            },
            "suggested_actions": [
                {"label": "Show overdue only", "value": "Show overdue invoices"},
                {"label": "Send reminders", "value": "send reminders to all overdue"},
            ],
        }
    }
