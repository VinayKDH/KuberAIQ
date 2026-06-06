"""Infrastructure adapter smoke tests (local mocks)."""
from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.domain.enums import ReminderChannel
from app.infrastructure.notifications.mock_notifier import MockNotifier
from app.infrastructure.storage.local_blob import LocalBlobStorage


@pytest.mark.asyncio
async def test_local_blob_roundtrip(tmp_path: Path) -> None:
    storage = LocalBlobStorage(base_dir=str(tmp_path))
    key = f"invoices/{uuid.uuid4()}.pdf"
    await storage.upload(key, b"pdf-bytes", content_type="application/pdf")
    data = await storage.download(key)
    assert data == b"pdf-bytes"
    url = await storage.get_signed_url(key, ttl_seconds=3600)
    assert key.replace("/", "%2F") in url or "invoices" in url


@pytest.mark.asyncio
async def test_mock_notifier_returns_provider_id() -> None:
    notifier = MockNotifier()
    msg_id = await notifier.send_message(
        channel=ReminderChannel.WHATSAPP,
        to="+919876543210",
        message="Payment reminder",
    )
    assert msg_id.startswith("mock-")
