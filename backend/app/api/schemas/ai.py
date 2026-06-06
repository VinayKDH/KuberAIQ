"""AI Copilot API schemas."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.core.constants import AI_MAX_MESSAGE_LEN


class ChatRequest(BaseModel):
    message: str = Field(max_length=AI_MAX_MESSAGE_LEN)
    session_id: str | None = None
    channel: str = "web"
    confirmed: bool = False


class SuggestedAction(BaseModel):
    label: str
    value: str


class ChatResponse(BaseModel):
    session_id: str
    intent: str
    message: str
    requires_confirmation: bool
    pending_action: dict[str, Any] | None = None
    data: dict[str, Any] | None = None
    suggested_actions: list[SuggestedAction] = Field(default_factory=list)


class ConfirmRequest(BaseModel):
    session_id: str
    pending_action: dict[str, Any]
