"""AI Copilot use-case orchestration — bridges API and LangGraph."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from app.application.services.collection_service import CollectionService
from app.application.services.customer_service import CreateCustomerInput, CustomerService
from app.application.services.dashboard_service import DashboardService
from app.application.services.invoice_service import CreateInvoiceInput, InvoiceItemInput, InvoiceService
from app.core.constants import AiIntent
from app.domain.enums import InvoiceStatus
from app.infrastructure.ai.graph.build import CopilotGraph


@dataclass
class ChatSession:
    id: str
    turns: list[dict[str, Any]] = field(default_factory=list)


class AiService:
    _sessions: dict[str, ChatSession] = {}

    def __init__(
        self,
        graph: CopilotGraph,
        customer_service: CustomerService,
        invoice_service: InvoiceService,
        collection_service: CollectionService,
        dashboard_service: DashboardService,
    ) -> None:
        self._graph = graph
        self._customer_service = customer_service
        self._invoice_service = invoice_service
        self._collection_service = collection_service
        self._dashboard_service = dashboard_service

    async def chat(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        message: str,
        session_id: str | None = None,
        channel: str = "web",
        confirmed: bool = False,
    ) -> dict[str, Any]:
        sid = session_id or str(uuid.uuid4())
        if sid not in self._sessions:
            self._sessions[sid] = ChatSession(id=sid)

        result = await self._graph.run(
            company_id=str(company_id),
            user_id=str(user_id),
            message=message,
            channel=channel,
            confirmed=confirmed,
            services={
                "customer": self._customer_service,
                "invoice": self._invoice_service,
                "collection": self._collection_service,
                "dashboard": self._dashboard_service,
            },
        )
        result["session_id"] = sid
        self._sessions[sid].turns.append({"user": message, "assistant": result})
        return result

    async def confirm(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        session_id: str,
        pending_action: dict[str, Any],
    ) -> dict[str, Any]:
        action_type = pending_action.get("type")
        preview = pending_action.get("preview", {})

        if action_type == AiIntent.CREATE_INVOICE:
            items = [
                InvoiceItemInput(
                    description=i["description"],
                    quantity=i["quantity"],
                    unit_price=i["unit_price"],
                    gst_rate=i["gst_rate"],
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
                    issue_date=preview["issue_date"],
                    due_date=preview["due_date"],
                    items=items,
                    status=InvoiceStatus(preview.get("status", "ISSUED")),
                ),
            )
            return {
                "intent": action_type,
                "message": f"Invoice {invoice.invoice_number} created successfully.",
                "requires_confirmation": False,
                "data": {"invoice_id": str(invoice.id), "invoice_number": invoice.invoice_number},
            }
        if action_type == AiIntent.CREATE_CUSTOMER:
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
            return {
                "intent": action_type,
                "message": f"Customer {customer.name} created.",
                "requires_confirmation": False,
                "data": {"customer_id": str(customer.id)},
            }
        return {
            "intent": action_type or AiIntent.CLARIFY,
            "message": "Action completed.",
            "requires_confirmation": False,
            "data": None,
        }

    def get_session(self, session_id: str) -> ChatSession | None:
        return self._sessions.get(session_id)
