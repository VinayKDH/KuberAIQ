"""Notifier hub with WhatsApp/SMS/Email channel routing."""
from __future__ import annotations

from app.domain.enums import ReminderChannel


class NotificationHub:
    def __init__(self, *, whatsapp, sms, email) -> None:
        self._whatsapp = whatsapp
        self._sms = sms
        self._email = email

    async def send_message(
        self,
        *,
        channel: ReminderChannel,
        to: str,
        message: str,
        template_name: str | None = None,
    ) -> str:
        if channel == ReminderChannel.WHATSAPP:
            return await self._whatsapp.send_message(
                channel=channel, to=to, message=message, template_name=template_name
            )
        if channel == ReminderChannel.SMS:
            return await self._sms.send_sms(to=to, message=message)
        if channel == ReminderChannel.EMAIL:
            return await self._email.send_email(
                to=to,
                subject="Payment reminder from KuberAIQ",
                body=message,
            )
        raise ValueError(f"Unsupported channel: {channel}")
