"""Invoice specialist agent."""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from app.application.ports.llm import LlmPort
from app.core.constants import AI_CLARIFY_SUGGESTED_ACTIONS, DEFAULT_DUE_DAYS, AiAwaiting, AiIntent
from app.domain.services.hsn_gst_lookup import resolve_product_tax_fields, suggest_hsn_from_name
from app.infrastructure.ai.conversation_context import build_clarify_pending
from app.infrastructure.ai.entity_extractor import extract_phone_from_text
from app.infrastructure.ai.tools.executor import ToolExecutor


def _format_item_summary(item: dict) -> str:
    qty = item["quantity"]
    unit = item.get("unit", "NOS")
    desc = item["description"]
    price = item.get("unit_price") or 0
    gst = item.get("gst_rate", 18)
    hsn = item.get("hsn_sac")
    hsn_part = f", HSN {hsn}" if hsn else ""
    return f"{qty} {unit} {desc} @ ₹{price} ({gst}% GST{hsn_part})"


async def _resolve_line_item(
    executor: ToolExecutor,
    company_id: uuid.UUID,
    raw: dict,
    global_gst: float | None,
) -> dict:
    description = raw.get("description") or "Item"
    product = await executor.find_product(company_id, description)
    unit_price = raw.get("unit_price")
    if unit_price is None and product:
        unit_price = float(product.default_price)

    hsn_sac = product.hsn_sac if product else None
    gst_rate = global_gst
    if gst_rate is None and product:
        gst_rate = float(product.gst_rate)

    if not hsn_sac or gst_rate is None:
        suggestion = suggest_hsn_from_name(description)
        if suggestion:
            hsn_sac = hsn_sac or suggestion.hsn_sac
            if gst_rate is None:
                gst_rate = float(suggestion.gst_rate)

    resolved_hsn, resolved_gst = resolve_product_tax_fields(
        name=description,
        hsn_sac=hsn_sac,
        gst_rate=Decimal(str(gst_rate)) if gst_rate is not None else None,
    )

    return {
        "description": product.name if product else description,
        "quantity": Decimal(str(raw.get("quantity") or 1)),
        "unit_price": Decimal(str(unit_price or 0)),
        "gst_rate": resolved_gst,
        "hsn_sac": resolved_hsn,
        "unit": raw.get("unit") or (product.unit if product else "NOS"),
        "product_id": str(product.id) if product else None,
    }


async def _build_invoice_draft(
    executor: ToolExecutor,
    company_id: uuid.UUID,
    entities: dict[str, Any],
) -> dict[str, Any]:
    raw_items = entities.get("line_items") or []
    if not raw_items:
        raw_items = [
            {
                "quantity": entities.get("quantity") or 1,
                "unit": entities.get("unit") or "NOS",
                "description": entities.get("description", "Item"),
                "unit_price": entities.get("unit_price"),
            }
        ]

    global_gst = entities.get("gst_rate")
    resolved_items = [
        await _resolve_line_item(executor, company_id, raw, global_gst) for raw in raw_items
    ]
    today = date.today()
    return {
        "issue_date": today,
        "due_date": today + timedelta(days=DEFAULT_DUE_DAYS),
        "status": "ISSUED",
        "items": resolved_items,
    }


def _customer_and_invoice_response(
    *,
    customer_name: str,
    phone: str,
    invoice_draft: dict[str, Any],
) -> dict:
    preview = {
        "customer": {"name": customer_name, "phone": phone},
        "invoice": invoice_draft,
    }
    item_lines = "\n".join(f"• {_format_item_summary(i)}" for i in invoice_draft["items"])

    return {
        "intent": AiIntent.CREATE_CUSTOMER_AND_INVOICE,
        "message": (
            f"I couldn't find '{customer_name}'. I'll add them with phone {phone} "
            f"and create the invoice:\n{item_lines}\n\nConfirm?"
        ),
        "requires_confirmation": True,
        "pending_action": {
            "type": AiIntent.CREATE_CUSTOMER_AND_INVOICE,
            "preview": preview,
        },
        "data": None,
        "suggested_actions": [
            {"label": "Confirm", "value": "confirm"},
            {"label": "Cancel", "value": "cancel"},
        ],
    }


async def run_invoice_agent(state: dict) -> dict:
    llm: LlmPort = state["llm"]
    entities = await llm.extract_entities(state["message"], "invoice")
    services = state.get("services", {})
    executor = ToolExecutor(services)
    company_id = uuid.UUID(state["company_id"])
    user_id = uuid.UUID(state["user_id"])

    clarify = state.get("clarify_pending") or {}
    clarify_inner = clarify.get("context") or {}
    if clarify.get("awaiting") == AiAwaiting.CREATE_MISSING_CUSTOMER:
        missing = clarify_inner.get("missing_customer")
        invoice_draft = clarify_inner.get("invoice_draft")
        phone = extract_phone_from_text(state.get("original_message") or state["message"])
        if missing and invoice_draft and phone:
            return {
                "response": _customer_and_invoice_response(
                    customer_name=missing,
                    phone=phone,
                    invoice_draft=invoice_draft,
                )
            }

    customer_name = entities.get("customer_name")
    if not customer_name:
        clarify_pending = build_clarify_pending(
            awaiting=AiAwaiting.INVOICE_CUSTOMER,
            context={},
        )
        return {
            "response": {
                "intent": AiIntent.CLARIFY,
                "message": (
                    "Which customer should I invoice? "
                    "Example: Invoice Manu Paneer for 10 kg paneer at 200"
                ),
                "requires_confirmation": False,
                "pending_action": clarify_pending,
                "data": None,
                "suggested_actions": list(AI_CLARIFY_SUGGESTED_ACTIONS),
            }
        }

    invoice_draft = await _build_invoice_draft(executor, company_id, entities)
    customers = await executor.find_customer(company_id, customer_name)

    if not customers:
        original_request = state.get("original_message") or state.get("message", "")
        phone = entities.get("customer_phone") or extract_phone_from_text(original_request)
        if phone:
            return {
                "response": _customer_and_invoice_response(
                    customer_name=customer_name,
                    phone=phone,
                    invoice_draft=invoice_draft,
                )
            }

        clarify_pending = build_clarify_pending(
            awaiting=AiAwaiting.CREATE_MISSING_CUSTOMER,
            context={
                "missing_customer": customer_name,
                "original_invoice_message": original_request,
                "invoice_draft": invoice_draft,
            },
        )
        return {
            "response": {
                "intent": AiIntent.CLARIFY,
                "message": (
                    f"I couldn't find '{customer_name}'. "
                    "Share their 10-digit phone and I'll add them and create the invoice."
                ),
                "requires_confirmation": False,
                "pending_action": clarify_pending,
                "data": {
                    "missing_customer": customer_name,
                    "original_invoice_message": original_request,
                },
                "suggested_actions": [
                    {
                        "label": f"Add {customer_name}",
                        "value": f"Add customer {customer_name} 9000000000",
                    },
                    {"label": "Find customers", "value": f"find customer {customer_name}"},
                ],
            }
        }

    customer = customers[0]
    preview = {
        "customer_id": str(customer.id),
        "customer_name": customer.name,
        **invoice_draft,
    }

    if state.get("confirmed"):
        result = await executor.create_invoice(company_id, user_id, preview)
        return {
            "response": {
                "intent": AiIntent.CREATE_INVOICE,
                "message": f"Invoice {result.get('invoice_number')} created.",
                "requires_confirmation": False,
                "pending_action": None,
                "data": result,
                "suggested_actions": [],
            }
        }

    item_lines = "\n".join(f"• {_format_item_summary(i)}" for i in invoice_draft["items"])
    return {
        "response": {
            "intent": AiIntent.CREATE_INVOICE,
            "message": (
                f"I'll create an invoice for {customer.name}:\n{item_lines}\n\nConfirm?"
            ),
            "requires_confirmation": True,
            "pending_action": {"type": AiIntent.CREATE_INVOICE, "preview": preview},
            "data": None,
            "suggested_actions": [
                {"label": "Confirm", "value": "confirm"},
                {"label": "Cancel", "value": "cancel"},
            ],
        }
    }
