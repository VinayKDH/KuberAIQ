"""WhatsApp webhook signature verification."""
from __future__ import annotations

import hashlib
import hmac

from app.core.config import settings


def verify_whatsapp_signature(payload: bytes, signature: str | None, secret: str | None) -> bool:
    """Validate Meta webhook `X-Hub-Signature-256` header."""
    if not secret:
        if settings.environment == "production" and not settings.use_mock_whatsapp:
            return False
        return True
    if not signature:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
