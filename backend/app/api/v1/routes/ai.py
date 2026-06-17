"""AI Copilot routes."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import AuthContext, get_tenant_context, get_container
from app.api.schemas.ai import ChatRequest, ChatResponse, ConfirmRequest, SuggestedAction
from app.core.container import Container

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> ChatResponse:
    result = await container.ai_service.chat(
        company_id=auth.company_id,
        user_id=auth.user_id,
        message=body.message,
        session_id=body.session_id,
        channel=body.channel,
        confirmed=body.confirmed,
        pending_action=body.pending_action,
    )
    return ChatResponse(
        session_id=result["session_id"],
        intent=result["intent"],
        message=result["message"],
        requires_confirmation=result["requires_confirmation"],
        pending_action=result.get("pending_action"),
        data=result.get("data"),
        suggested_actions=[SuggestedAction(**a) for a in result.get("suggested_actions", [])],
    )


@router.post("/confirm", response_model=ChatResponse)
async def confirm_action(
    body: ConfirmRequest,
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> ChatResponse:
    result = await container.ai_service.confirm(
        company_id=auth.company_id,
        user_id=auth.user_id,
        session_id=body.session_id,
        pending_action=body.pending_action,
    )
    return ChatResponse(
        session_id=body.session_id,
        intent=result["intent"],
        message=result["message"],
        requires_confirmation=result["requires_confirmation"],
        pending_action=result.get("pending_action"),
        data=result.get("data"),
        suggested_actions=[SuggestedAction(**a) for a in result.get("suggested_actions", [])],
    )


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> dict:
    session = await container.ai_service.get_session(auth.company_id, session_id)
    if not session:
        return {"turns": []}
    async with container.uow_factory() as uow:
        turns = await uow.ai_sessions.list_recent_turns(
            session_id, company_id=auth.company_id, limit=20
        )
    return {"session_id": session.id, "turns": turns}


@router.post("/voice")
async def voice_copilot(
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
    audio: UploadFile = File(...),
) -> dict:
    _ = await audio.read()
    # MVP Azure Speech stub: treat as non-transcribed input.
    result = await container.ai_service.chat(
        company_id=auth.company_id,
        user_id=auth.user_id,
        message="(voice input received)",
        channel="voice",
    )
    return {"transcript": None, "stub": True, "response": result}
