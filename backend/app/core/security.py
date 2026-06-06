"""JWT minting/validation. HS256 for local/dev; swap to RS256 + Key Vault in prod."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import settings
from app.core.constants import ACCESS_TOKEN_TTL_MINUTES, REFRESH_TOKEN_TTL_DAYS
from app.core.errors import UnauthorizedError


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(*, user_id: str, company_id: str, role: str) -> str:
    expire = _now() + timedelta(minutes=ACCESS_TOKEN_TTL_MINUTES)
    payload = {
        "sub": user_id,
        "company_id": company_id,
        "role": role,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "exp": expire,
        "iat": _now(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(*, user_id: str) -> str:
    expire = _now() + timedelta(days=REFRESH_TOKEN_TTL_DAYS)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "exp": expire,
        "iat": _now(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:  # pragma: no cover - exercised via API tests
        raise UnauthorizedError("Invalid or expired token") from exc
