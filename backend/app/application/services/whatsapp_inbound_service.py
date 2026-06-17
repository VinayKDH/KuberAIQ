"""Route inbound WhatsApp messages to the AI copilot and reply on-thread."""
from __future__ import annotations

from typing import Any

import structlog

from app.application.services.ai_service import AiService
from app.application.services.billing_service import BillingService
from app.application.ports.notifier import NotifierPort
from app.core.constants import WHATSAPP_COPILOT_MAX_REPLY_CHARS, WHATSAPP_COPILOT_UNLINKED_REPLY
from app.domain.enums import ReminderChannel
from app.infrastructure.notifications.phone_utils import normalize_whatsapp_phone

logger = structlog.get_logger(__name__)


class WhatsappInboundService:
    def __init__(
        self,
        uow_factory,
        ai_service: AiService,
        billing_service: BillingService,
        notifier: NotifierPort,
    ) -> None:
        self._uow_factory = uow_factory
        self._ai = ai_service
        self._billing = billing_service
        self._notifier = notifier

    async def handle_payload(self, payload: dict[str, Any]) -> dict[str, int]:
        entries = payload.get("entry", [])
        messages_handled = 0
        statuses_logged = 0

        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for status in value.get("statuses", []):
                    statuses_logged += 1
                    logger.info(
                        "whatsapp_status_update",
                        message_id=status.get("id"),
                        status=status.get("status"),
                        recipient=status.get("recipient_id"),
                    )
                for message in value.get("messages", []):
                    if await self._handle_message(message):
                        messages_handled += 1

        return {
            "entries": len(entries),
            "messages_handled": messages_handled,
            "statuses_logged": statuses_logged,
        }

    async def _handle_message(self, message: dict[str, Any]) -> bool:
        if message.get("type") != "text":
            logger.info("whatsapp_inbound_skipped", reason="non_text", type=message.get("type"))
            return False

        phone = normalize_whatsapp_phone(message.get("from"))
        body = (message.get("text") or {}).get("body", "").strip()
        if not phone or not body:
            return False

        async with self._uow_factory() as uow:
            user = await uow.users.find_owner_by_whatsapp_phone(phone)

        if not user or not user.company_id:
            await self._send_text(phone, WHATSAPP_COPILOT_UNLINKED_REPLY)
            return True

        if not await self._billing.is_active(user.id):
            await self._send_text(
                phone,
                "Your KuberAIQ subscription is inactive. Renew at https://www.kuberaiq.com/settings",
            )
            return True

        session_id = f"wa-{phone}"
        result = await self._ai.chat(
            company_id=user.company_id,
            user_id=user.id,
            message=body,
            session_id=session_id,
            channel="whatsapp",
        )
        reply = self._format_reply(result)
        await self._send_text(phone, reply)
        logger.info(
            "whatsapp_copilot_reply",
            user_id=str(user.id),
            company_id=str(user.company_id),
            intent=result.get("intent"),
        )
        return True

    def _format_reply(self, result: dict[str, Any]) -> str:
        text = str(result.get("message") or "I could not process that request.")
        if result.get("requires_confirmation"):
            text = f"{text}\n\nReply YES to confirm or NO to cancel."
        if len(text) > WHATSAPP_COPILOT_MAX_REPLY_CHARS:
            text = text[: WHATSAPP_COPILOT_MAX_REPLY_CHARS - 3] + "..."
        return text

    async def _send_text(self, phone: str, message: str) -> None:
        try:
            await self._notifier.send_message(
                channel=ReminderChannel.WHATSAPP,
                to=phone,
                message=message,
            )
        except Exception as exc:
            logger.warning("whatsapp_reply_failed", phone=phone, error=str(exc))
