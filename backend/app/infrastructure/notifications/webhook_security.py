"""WhatsApp webhook signature verification."""
from __future__ import annotations

import hashlib
import hmac


def verify_whatsapp_signature(payload: bytes, signature: str | None, secret: str | None) -> bool:
    """Validate Meta webhook `X-Hub-Signature-256` header."""
    if not secret:
        return True
    if not signature:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
