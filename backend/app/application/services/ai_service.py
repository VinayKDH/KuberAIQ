"""AI Copilot use-case orchestration — bridges API and LangGraph."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from app.application.services.collection_service import CollectionService
from app.application.services.customer_service import CreateCustomerInput, CustomerService
from app.application.services.dashboard_service import DashboardService
from app.application.services.invoice_service import CreateInvoiceInput, InvoiceItemInput, InvoiceService
from app.core.constants import AI_HISTORY_TURNS, AI_SOFT_TOKEN_BUDGET_MONTHLY, AiIntent
from app.infrastructure.ai.conversation_context import is_confirmable_pending
from app.domain.enums import InvoiceStatus
from app.infrastructure.ai.graph.build import CopilotGraph
from app.infrastructure.ai.interaction_logger import log_ai_confirm, log_ai_interaction

_CONFIRM_WORDS = frozenset({"yes", "confirm", "ok", "proceed", "go ahead"})
_CANCEL_WORDS = frozenset({"no", "cancel", "stop", "abort"})


def _parse_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _decimal(value: Decimal | float | int | str) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


class AiService:
    def __init__(
        self,
        graph: CopilotGraph,
        uow_factory,
        customer_service: CustomerService,
        invoice_service: InvoiceService,
        collection_service: CollectionService,
        dashboard_service: DashboardService,
        product_service=None,
    ) -> None:
        self._graph = graph
        self._uow_factory = uow_factory
        self._customer_service = customer_service
        self._invoice_service = invoice_service
        self._collection_service = collection_service
        self._dashboard_service = dashboard_service
        self._product_service = product_service

    async def chat(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        message: str,
        session_id: str | None = None,
        channel: str = "web",
        confirmed: bool = False,
        pending_action: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        sid = session_id or str(uuid.uuid4())
        async with self._uow_factory() as uow:
            session = await uow.ai_sessions.create_or_touch_session(
                sid, company_id=company_id, user_id=user_id
            )

        normalized = message.strip().lower()
        clarify_pending = (
            session.pending_action
            if session.pending_action and session.pending_action.get("type") == AiIntent.CLARIFY
            else None
        )
        action_to_confirm = pending_action or session.pending_action
        if not is_confirmable_pending(action_to_confirm):
            action_to_confirm = None

        if not confirmed and action_to_confirm:
            if normalized in _CONFIRM_WORDS:
                return await self.confirm(
                    company_id=company_id,
                    user_id=user_id,
                    session_id=sid,
                    pending_action=action_to_confirm,
                )
            if normalized in _CANCEL_WORDS:
                async with self._uow_factory() as uow:
                    await uow.ai_sessions.set_pending_action(sid, company_id, None)
                return {
                    "session_id": sid,
                    "intent": AiIntent.CLARIFY,
                    "message": "Okay, I cancelled that action.",
                    "requires_confirmation": False,
                    "pending_action": None,
                    "data": None,
                    "suggested_actions": [],
                }

        async with self._uow_factory() as uow:
            history = await uow.ai_sessions.list_recent_turns(
                sid, company_id=company_id, limit=AI_HISTORY_TURNS
            )
        result = await self._graph.run(
            company_id=str(company_id),
            user_id=str(user_id),
            message=message,
            channel=channel,
            confirmed=confirmed,
            history=history,
            clarify_pending=clarify_pending,
            services={
                "customer": self._customer_service,
                "invoice": self._invoice_service,
                "collection": self._collection_service,
                "dashboard": self._dashboard_service,
                "product": self._product_service,
            },
        )
        result["session_id"] = sid
        pending_action_payload = result.get("pending_action") or {}
        if result.get("requires_confirmation"):
            pending = result.get("pending_action")
        elif pending_action_payload.get("type") == AiIntent.CLARIFY:
            pending = result.get("pending_action")
        elif result.get("intent") != AiIntent.CLARIFY:
            pending = None
        else:
            pending = clarify_pending
        async with self._uow_factory() as uow:
            await uow.ai_sessions.set_pending_action(sid, company_id, pending)
            await uow.ai_sessions.append_turn(
                sid,
                company_id=company_id,
                user_message=message,
                assistant_payload=result,
            )
            tokens_in = len(message.split())
            tokens_out = len(str(result.get("message", "")).split())
            total_tokens = tokens_in + tokens_out
            await uow.ai_usage.add_usage(
                company_id=company_id,
                session_id=sid,
                model_name=self._graph.model_name,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                total_tokens=total_tokens,
            )
            monthly = await uow.ai_usage.total_tokens_this_month(company_id)
        if monthly >= AI_SOFT_TOKEN_BUDGET_MONTHLY:
            result["message"] = (
                f"{result.get('message', '')}\n\n"
                "Usage note: monthly AI budget soft cap reached; responses may be simplified."
            ).strip()
        log_ai_interaction(
            company_id=str(company_id),
            user_id=str(user_id),
            session_id=sid,
            channel=channel,
            message=message,
            route=result.pop("route", None),
            intent=str(result.get("intent", "")),
            requires_confirmation=bool(result.get("requires_confirmation")),
            clarified=result.get("intent") == AiIntent.CLARIFY,
        )
        return result

    async def confirm(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        session_id: str,
        pending_action: dict[str, Any],
    ) -> dict[str, Any]:
        async with self._uow_factory() as uow:
            session = await uow.ai_sessions.get_session(session_id, company_id)
        action_type = pending_action.get("type")
        preview = pending_action.get("preview", {})

        if action_type == AiIntent.CREATE_INVOICE:
            items = [
                InvoiceItemInput(
                    description=i["description"],
                    quantity=_decimal(i["quantity"]),
                    unit_price=_decimal(i["unit_price"]),
                    gst_rate=_decimal(i["gst_rate"]),
                    hsn_sac=i.get("hsn_sac"),
                    unit=i.get("unit", "NOS"),
                )
                for i in preview.get("items", [])
            ]
            invoice = await self._invoice_service.create(
                company_id=company_id,
                actor_id=user_id,
                data=CreateInvoiceInput(
                    customer_id=uuid.UUID(preview["customer_id"]),
                    issue_date=_parse_date(preview["issue_date"]),
                    due_date=_parse_date(preview["due_date"]),
                    items=items,
                    status=InvoiceStatus(preview.get("status", "ISSUED")),
                ),
            )
            result = {
                "session_id": session_id,
                "intent": action_type,
                "message": f"Invoice {invoice.invoice_number} created successfully.",
                "requires_confirmation": False,
                "pending_action": None,
                "data": {"invoice_id": str(invoice.id), "invoice_number": invoice.invoice_number},
                "suggested_actions": [],
            }
        elif action_type == AiIntent.CREATE_CUSTOMER:
            customer = await self._customer_service.create(
                company_id=company_id,
                actor_id=user_id,
                data=CreateCustomerInput(
                    name=preview["name"],
                    phone=preview["phone"],
                    gstin=preview.get("gstin"),
                    billing_address=preview.get("billing_address"),
                ),
            )
            result = {
                "session_id": session_id,
                "intent": action_type,
                "message": f"Customer {customer.name} created.",
                "requires_confirmation": False,
                "pending_action": None,
                "data": {"customer_id": str(customer.id), "name": customer.name},
                "suggested_actions": [],
            }
        elif action_type == AiIntent.CREATE_CUSTOMER_AND_INVOICE:
            from app.infrastructure.ai.tools.executor import ToolExecutor

            executor = ToolExecutor(
                {
                    "customer": self._customer_service,
                    "invoice": self._invoice_service,
                }
            )
            combined = await executor.create_customer_and_invoice(
                company_id, user_id, preview
            )
            result = {
                "session_id": session_id,
                "intent": action_type,
                "message": (
                    f"Customer {combined['customer_name']} created. "
                    f"Invoice {combined['invoice_number']} created successfully."
                ),
                "requires_confirmation": False,
                "pending_action": None,
                "data": combined,
                "suggested_actions": [],
            }
        elif action_type == AiIntent.BULK_SEND_REMINDERS:
            reminders = await self._collection_service.bulk_send(
                company_id=company_id,
                actor_id=user_id,
            )
            result = {
                "session_id": session_id,
                "intent": action_type,
                "message": f"Sent {len(reminders)} WhatsApp reminders.",
                "requires_confirmation": False,
                "pending_action": None,
                "data": {"sent_count": len(reminders)},
                "suggested_actions": [],
            }
        else:
            result = {
                "session_id": session_id,
                "intent": action_type or AiIntent.CLARIFY,
                "message": "Action completed.",
                "requires_confirmation": False,
                "pending_action": None,
                "data": None,
                "suggested_actions": [],
            }

        if session:
            async with self._uow_factory() as uow:
                await uow.ai_sessions.set_pending_action(session_id, company_id, None)
                await uow.ai_sessions.append_turn(
                    session_id,
                    company_id=company_id,
                    user_message="confirm",
                    assistant_payload=result,
                )
        log_ai_confirm(
            company_id=str(company_id),
            user_id=str(user_id),
            session_id=session_id,
            action_type=action_type,
            success=result.get("intent") not in {None, AiIntent.CLARIFY},
            detail=result.get("data"),
        )
        return result

    async def get_session(self, company_id: uuid.UUID, session_id: str):
        async with self._uow_factory() as uow:
            return await uow.ai_sessions.get_session(session_id, company_id)
