"""Google OAuth (OIDC) auth adapter."""
from __future__ import annotations

import uuid

import httpx
import structlog
from jose import jwk, jwt
from jose.exceptions import JWTError

from app.application.ports.repositories import SubscriptionRecord, UserRecord
from app.core.config import settings
from app.core.constants import SUBSCRIPTION_PLAN_STARTER
from app.domain.enums import SubscriptionStatus
from app.core.constants import (
    GOOGLE_OAUTH_ISSUERS,
    GOOGLE_OAUTH_JWKS_URL,
    GOOGLE_OAUTH_TOKEN_URL,
)
from app.core.errors import UnauthorizedError, ValidationAppError
from app.domain.enums import UserRole
from app.infrastructure.auth.token_service import TokenService

logger = structlog.get_logger(__name__)

_JWKS_CACHE: dict | None = None


class GoogleAuthProvider:
    def __init__(self, uow_factory, tokens: TokenService | None = None) -> None:
        self._uow_factory = uow_factory
        self._tokens = tokens or TokenService()

    async def exchange_google_code(
        self,
        *,
        code: str,
        code_verifier: str,
        redirect_uri: str,
    ) -> dict:
        if not settings.google_client_id:
            raise ValidationAppError("Google OAuth is not configured")
        if not settings.google_client_secret:
            raise ValidationAppError("Google client secret is required for server-side token exchange")

        payload = {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(GOOGLE_OAUTH_TOKEN_URL, data=payload)
            if response.status_code >= 400:
                raise UnauthorizedError("Google token exchange failed")
            body = response.json()

        id_token = body.get("id_token")
        if not id_token:
            raise UnauthorizedError("Google response missing id_token")

        claims = await self._validate_id_token(id_token, access_token=body.get("access_token"))
        google_sub = claims.get("sub")
        email = (claims.get("email") or "").lower()
        full_name = claims.get("name")
        email_verified = claims.get("email_verified", False)
        if not google_sub or not email:
            raise UnauthorizedError("Google token missing required claims")
        if not email_verified:
            raise UnauthorizedError("Google email is not verified")

        async with self._uow_factory() as uow:
            user = await uow.users.get_by_google_sub(google_sub)
            if not user:
                existing = await uow.users.get_by_email(email)
                if existing:
                    user = await uow.users.link_google_sub(existing.id, google_sub)
                else:
                    user = await uow.users.create(
                        UserRecord(
                            id=uuid.uuid4(),
                            company_id=None,
                            google_sub=google_sub,
                            email=email,
                            full_name=full_name,
                            role=UserRole.OWNER,
                        )
                    )
                    await uow.subscriptions.create(
                        SubscriptionRecord(
                            id=uuid.uuid4(),
                            user_id=user.id,
                            status=SubscriptionStatus.PENDING,
                            plan_code=SUBSCRIPTION_PLAN_STARTER,
                            amount_paise=settings.subscription_plan_amount_paise,
                        )
                    )
                await uow.commit()
        return self._tokens.issue_tokens(user)

    async def _validate_id_token(self, id_token: str, *, access_token: str | None = None) -> dict:
        global _JWKS_CACHE

        try:
            header = jwt.get_unverified_header(id_token)
            kid = header.get("kid")
            key = await self._resolve_jwk(kid)
            public_key = jwk.construct(key)
            claims = jwt.decode(
                id_token,
                public_key,
                algorithms=["RS256"],
                audience=settings.google_client_id,
                access_token=access_token,
                options={"verify_iss": False, "verify_at_hash": bool(access_token)},
            )
            if claims.get("iss") not in GOOGLE_OAUTH_ISSUERS:
                raise UnauthorizedError("Invalid Google token issuer")
            return claims
        except JWTError as exc:
            logger.warning("google_id_token_invalid", error=str(exc))
            raise UnauthorizedError("Invalid Google id_token") from exc

    async def _resolve_jwk(self, kid: str | None) -> dict:
        global _JWKS_CACHE

        async def fetch_jwks() -> dict:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(GOOGLE_OAUTH_JWKS_URL)
                response.raise_for_status()
                return response.json()

        if _JWKS_CACHE is None:
            _JWKS_CACHE = await fetch_jwks()

        if kid:
            key = next((k for k in _JWKS_CACHE["keys"] if k.get("kid") == kid), None)
            if key:
                return key

        _JWKS_CACHE = await fetch_jwks()
        key = next((k for k in _JWKS_CACHE["keys"] if k.get("kid") == kid), None)
        if not key:
            raise UnauthorizedError("Signing key not found")
        return key
