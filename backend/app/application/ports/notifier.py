"""Notification port — WhatsApp/SMS/email abstraction."""
from __future__ import annotations

from typing import Protocol

from app.domain.enums import ReminderChannel


class NotifierPort(Protocol):
    async def send_message(
        self,
        *,
        channel: ReminderChannel,
        to: str,
        message: str,
        template_name: str | None = None,
    ) -> str: ...
