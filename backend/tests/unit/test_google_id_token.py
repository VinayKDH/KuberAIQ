"""Unit tests for Google OAuth id_token validation."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.constants import GOOGLE_OAUTH_ISSUERS
from app.core.errors import UnauthorizedError
from app.infrastructure.auth.google_auth import GoogleAuthProvider


@pytest.mark.asyncio
async def test_validate_id_token_rejects_unknown_issuer() -> None:
    provider = GoogleAuthProvider(uow_factory=lambda: None)

    with patch("app.infrastructure.auth.google_auth.jwt.get_unverified_header", return_value={"kid": "kid1"}):
        with patch.object(provider, "_resolve_jwk", return_value={"kid": "kid1"}):
            with patch("app.infrastructure.auth.google_auth.jwk.construct"):
                with patch(
                    "app.infrastructure.auth.google_auth.jwt.decode",
                    return_value={"iss": "https://evil.example.com", "sub": "1", "email": "a@b.com"},
                ):
                    with pytest.raises(UnauthorizedError, match="Invalid Google token issuer"):
                        await provider._validate_id_token("token", access_token="access")


@pytest.mark.asyncio
async def test_validate_id_token_accepts_google_issuer() -> None:
    provider = GoogleAuthProvider(uow_factory=lambda: None)
    claims = {
        "iss": GOOGLE_OAUTH_ISSUERS[0],
        "sub": "google-sub-123",
        "email": "user@example.com",
        "email_verified": True,
        "name": "Test User",
    }

    with patch("app.infrastructure.auth.google_auth.jwt.get_unverified_header", return_value={"kid": "kid1"}):
        with patch.object(provider, "_resolve_jwk", return_value={"kid": "kid1"}):
            with patch("app.infrastructure.auth.google_auth.jwk.construct"):
                with patch("app.infrastructure.auth.google_auth.jwt.decode", return_value=claims) as decode:
                    result = await provider._validate_id_token("token", access_token="google-access")
                    assert result["sub"] == "google-sub-123"
                    assert decode.call_args.kwargs["access_token"] == "google-access"


@pytest.mark.asyncio
async def test_validate_id_token_skips_at_hash_without_access_token() -> None:
    provider = GoogleAuthProvider(uow_factory=lambda: None)

    with patch("app.infrastructure.auth.google_auth.jwt.get_unverified_header", return_value={"kid": "kid1"}):
        with patch.object(provider, "_resolve_jwk", return_value={"kid": "kid1"}):
            with patch("app.infrastructure.auth.google_auth.jwk.construct"):
                with patch("app.infrastructure.auth.google_auth.jwt.decode", return_value={"iss": GOOGLE_OAUTH_ISSUERS[0]}) as decode:
                    await provider._validate_id_token("token", access_token=None)
                    assert decode.call_args.kwargs["options"]["verify_at_hash"] is False
