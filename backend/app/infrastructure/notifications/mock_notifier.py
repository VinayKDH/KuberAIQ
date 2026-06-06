"""Mock notifier for local development."""
from __future__ import annotations

import uuid

import structlog

from app.domain.enums import ReminderChannel

logger = structlog.get_logger(__name__)


class MockNotifier:
    async def send_message(
        self,
        *,
        channel: ReminderChannel,
        to: str,
        message: str,
        template_name: str | None = None,
    ) -> str:
        provider_id = f"mock-{channel.lower()}-{uuid.uuid4().hex[:12]}"
        logger.info(
            "mock_notification_sent",
            channel=channel,
            to=to,
            message=message[:100],
            provider_id=provider_id,
        )
        return provider_id
