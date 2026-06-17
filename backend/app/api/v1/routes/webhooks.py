"""WhatsApp inbound message routing to AI copilot."""
from __future__ import annotations

import structlog
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from app.api.deps import get_container
from app.core.config import settings
from app.core.constants import WHATSAPP_HUB_MODE, WHATSAPP_SIGNATURE_HEADER
from app.core.container import Container
from app.infrastructure.notifications.webhook_security import verify_whatsapp_signature

logger = structlog.get_logger(__name__)

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
async def whatsapp_inbound(
    request: Request,
    container: Annotated[Container, Depends(get_container)],
) -> dict:
    raw = await request.body()
    signature = request.headers.get(WHATSAPP_SIGNATURE_HEADER)
    if not verify_whatsapp_signature(raw, signature, settings.whatsapp_app_secret):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    body = await request.json()
    result = await container.whatsapp_inbound_service.handle_payload(body)
    return {"status": "received", **result}
