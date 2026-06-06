"""LangGraph shared state definition."""
from __future__ import annotations

from typing import Any, Literal, TypedDict


class CopilotState(TypedDict, total=False):
    company_id: str
    user_id: str
    channel: Literal["web", "whatsapp", "voice"]
    message: str
    intent: str | None
    route: str | None
    entities: dict[str, Any] | None
    pending_action: dict[str, Any] | None
    confirmed: bool
    result: dict[str, Any] | None
    response: dict[str, Any] | None
    services: dict[str, Any]
