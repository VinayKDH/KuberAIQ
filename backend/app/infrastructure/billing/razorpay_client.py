"""Razorpay REST client for subscription checkout."""
from __future__ import annotations

import base64
import hashlib
import hmac

import httpx

from app.core.config import settings
from app.core.constants import RAZORPAY_API_BASE_URL
from app.core.errors import ValidationAppError


class RazorpayClient:
    def __init__(self) -> None:
        if not settings.razorpay_key_id or not settings.razorpay_key_secret:
            raise ValidationAppError("Razorpay is not configured")
        token = base64.b64encode(
            f"{settings.razorpay_key_id}:{settings.razorpay_key_secret}".encode()
        ).decode()
        self._headers = {"Authorization": f"Basic {token}"}

    async def create_order(self, *, amount_paise: int, receipt: str, notes: dict[str, str]) -> dict:
        payload = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "notes": notes,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{RAZORPAY_API_BASE_URL}/orders",
                json=payload,
                headers=self._headers,
            )
            if response.status_code >= 400:
                raise ValidationAppError("Failed to create Razorpay order")
            return response.json()

    def verify_payment_signature(
        self, *, order_id: str, payment_id: str, signature: str
    ) -> bool:
        secret = settings.razorpay_key_secret or ""
        body = f"{order_id}|{payment_id}".encode()
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        secret = settings.razorpay_webhook_secret or settings.razorpay_key_secret or ""
        if not secret:
            return False
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
