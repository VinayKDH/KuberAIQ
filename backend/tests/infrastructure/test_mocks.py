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


@pytest.mark.asyncio
async def test_whatsapp_notifier_posts_to_graph_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.core import config as config_mod
    from app.infrastructure.notifications.whatsapp_notifier import WhatsAppNotifier

    monkeypatch.setattr(config_mod.settings, "whatsapp_phone_number_id", "123456")
    monkeypatch.setattr(config_mod.settings, "whatsapp_access_token", "token")

    captured: dict = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"messages": [{"id": "wamid.real"}]}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, json, headers):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return FakeResponse()

    monkeypatch.setattr(
        "app.infrastructure.notifications.whatsapp_notifier.httpx.AsyncClient",
        lambda **kwargs: FakeClient(),
    )

    notifier = WhatsAppNotifier()
    provider_id = await notifier.send_message(
        channel=ReminderChannel.WHATSAPP,
        to="+919876543210",
        message="Invoice reminder",
    )
    assert provider_id == "wamid.real"
    assert "123456/messages" in captured["url"]
    assert captured["json"]["to"] == "919876543210"
