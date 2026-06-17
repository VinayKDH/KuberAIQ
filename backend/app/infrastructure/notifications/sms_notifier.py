"""SMS notifier adapters."""
from __future__ import annotations

import uuid

import structlog

logger = structlog.get_logger(__name__)


class MockSmsNotifier:
    async def send_sms(self, *, to: str, message: str) -> str:
        provider_id = f"mock-sms-{uuid.uuid4().hex[:12]}"
        logger.info("mock_sms_sent", to=to, provider_id=provider_id, message=message[:120])
        return provider_id


class SmsNotifier:
    async def send_sms(self, *, to: str, message: str) -> str:
        # MVP stub adapter: replace with provider integration.
        provider_id = f"sms-stub-{uuid.uuid4().hex[:12]}"
        logger.info("sms_stub_sent", to=to, provider_id=provider_id, message=message[:120])
        return provider_id
