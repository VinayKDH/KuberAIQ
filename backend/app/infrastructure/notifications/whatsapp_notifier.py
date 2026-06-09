"""WhatsApp Cloud API notifier adapter."""
from __future__ import annotations

import httpx
import structlog

from app.core.config import settings
from app.core.constants import WHATSAPP_GRAPH_API_VERSION, WHATSAPP_GRAPH_BASE_URL
from app.core.errors import ValidationAppError
from app.domain.enums import ReminderChannel

logger = structlog.get_logger(__name__)


class WhatsAppNotifier:
    async def send_message(
        self,
        *,
        channel: ReminderChannel,
        to: str,
        message: str,
        template_name: str | None = None,
    ) -> str:
        if channel is not ReminderChannel.WHATSAPP:
            raise ValidationAppError(f"Unsupported channel: {channel}")
        if not settings.whatsapp_phone_number_id or not settings.whatsapp_access_token:
            raise ValidationAppError("WhatsApp Cloud API is not configured")

        url = (
            f"{WHATSAPP_GRAPH_BASE_URL}/{WHATSAPP_GRAPH_API_VERSION}/"
            f"{settings.whatsapp_phone_number_id}/messages"
        )
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to.lstrip("+"),
            "type": "text",
            "text": {"preview_url": False, "body": message},
        }
        headers = {"Authorization": f"Bearer {settings.whatsapp_access_token}"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()

        provider_id = body["messages"][0]["id"]
        logger.info("whatsapp_message_sent", to=to, provider_id=provider_id)
        return provider_id

    def template_for_language(self, language: str) -> str:
        from app.core.constants import (
            WHATSAPP_TEMPLATE_REMINDER_EN,
            WHATSAPP_TEMPLATE_REMINDER_HI,
        )

        return WHATSAPP_TEMPLATE_REMINDER_HI if language == "hi" else WHATSAPP_TEMPLATE_REMINDER_EN
