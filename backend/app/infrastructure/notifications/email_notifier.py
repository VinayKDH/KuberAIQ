"""Email notifier adapters."""
from __future__ import annotations

import uuid

import structlog

logger = structlog.get_logger(__name__)


class MockEmailNotifier:
    async def send_email(self, *, to: str, subject: str, body: str) -> str:
        provider_id = f"mock-email-{uuid.uuid4().hex[:12]}"
        logger.info("mock_email_sent", to=to, provider_id=provider_id, subject=subject)
        return provider_id


class EmailNotifier:
    async def send_email(self, *, to: str, subject: str, body: str) -> str:
        # MVP stub adapter: replace with transactional email provider.
        provider_id = f"email-stub-{uuid.uuid4().hex[:12]}"
        logger.info("email_stub_sent", to=to, provider_id=provider_id, subject=subject)
        return provider_id
