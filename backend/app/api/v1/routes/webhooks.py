"""Webhook routes — WhatsApp inbound and status callbacks."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response

from app.core.config import settings
from app.core.constants import WHATSAPP_HUB_MODE

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("/whatsapp")
async def whatsapp_verify(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> Response:
    if hub_mode == WHATSAPP_HUB_MODE and hub_verify_token == settings.whatsapp_verify_token:
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(status_code=403)


@router.post("/whatsapp")
async def whatsapp_inbound(request: Request) -> dict:
    body = await request.json()
    return {"status": "received", "entries": len(body.get("entry", []))}
