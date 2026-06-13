"""Webhook API tests."""
from __future__ import annotations

import hashlib
import hmac
import json

import pytest
from httpx import AsyncClient

from app.core.config import settings


def _signature(payload: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


@pytest.mark.asyncio
async def test_whatsapp_webhook_verify(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.whatsapp_verify_token,
            "hub.challenge": "123456",
        },
    )
    assert response.status_code == 200
    assert response.text == "123456"


@pytest.mark.asyncio
async def test_whatsapp_webhook_inbound_without_secret(client: AsyncClient) -> None:
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "statuses": [{"id": "wamid.test", "status": "delivered"}],
                            "messages": [],
                        }
                    }
                ]
            }
        ]
    }
    response = await client.post("/api/v1/webhooks/whatsapp", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "received"
    assert body["processed"] == 1


@pytest.mark.asyncio
async def test_whatsapp_webhook_rejects_bad_signature(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core import config as config_mod

    monkeypatch.setattr(config_mod.settings, "whatsapp_app_secret", "test-secret")
    payload = {"entry": []}
    raw = json.dumps(payload).encode()
    response = await client.post(
        "/api/v1/webhooks/whatsapp",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": "sha256=bad",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_whatsapp_webhook_accepts_valid_signature(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core import config as config_mod

    secret = "test-secret"
    monkeypatch.setattr(config_mod.settings, "whatsapp_app_secret", secret)
    payload = {"entry": [{"changes": [{"value": {"statuses": [], "messages": []}}]}]}
    raw = json.dumps(payload).encode()
    response = await client.post(
        "/api/v1/webhooks/whatsapp",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": _signature(raw, secret),
        },
    )
    assert response.status_code == 200
