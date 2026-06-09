"""Structured logging for AI copilot interactions (queryable in App Insights)."""
from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


def log_ai_interaction(
    *,
    company_id: str,
    user_id: str,
    session_id: str,
    channel: str,
    message: str,
    route: str | None,
    intent: str,
    requires_confirmation: bool,
    clarified: bool,
) -> None:
    logger.info(
        "ai_chat_interaction",
        company_id=company_id,
        user_id=user_id,
        session_id=session_id,
        channel=channel,
        message_preview=message[:200],
        route=route,
        intent=intent,
        requires_confirmation=requires_confirmation,
        clarified=clarified,
    )


def log_ai_confirm(
    *,
    company_id: str,
    user_id: str,
    session_id: str,
    action_type: str | None,
    success: bool,
    detail: dict[str, Any] | None = None,
) -> None:
    logger.info(
        "ai_chat_confirm",
        company_id=company_id,
        user_id=user_id,
        session_id=session_id,
        action_type=action_type,
        success=success,
        detail=detail or {},
    )
