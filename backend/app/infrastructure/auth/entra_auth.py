"""Microsoft Entra ID (OIDC) auth adapter."""
from __future__ import annotations

import uuid

import httpx
from jose import jwt
from jose.exceptions import JWTError

from app.application.ports.repositories import SubscriptionRecord, UserRecord
from app.core.config import settings
from app.core.constants import SUBSCRIPTION_PLAN_STARTER
from app.domain.enums import SubscriptionStatus
from app.core.errors import UnauthorizedError, ValidationAppError
from app.domain.enums import UserRole
from app.infrastructure.auth.token_service import TokenService

_JWKS_CACHE: dict | None = None


class EntraAuthProvider:
    def __init__(self, uow_factory, tokens: TokenService | None = None) -> None:
        self._uow_factory = uow_factory
        self._tokens = tokens or TokenService()

    async def login(self, user: UserRecord) -> dict:
        return self._tokens.issue_tokens(user)

    async def exchange_entra_code(
        self,
        *,
        code: str,
        code_verifier: str,
        redirect_uri: str,
    ) -> dict:
        if not settings.entra_tenant_id or not settings.entra_client_id:
            raise ValidationAppError("Entra ID is not configured")
        if not settings.entra_client_secret:
            raise ValidationAppError("Entra client secret is required for server-side token exchange")

        token_url = (
            f"https://login.microsoftonline.com/{settings.entra_tenant_id}/oauth2/v2.0/token"
        )
        payload = {
            "client_id": settings.entra_client_id,
            "client_secret": settings.entra_client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(token_url, data=payload)
            if response.status_code >= 400:
                raise UnauthorizedError("Entra token exchange failed")
            body = response.json()

        id_token = body.get("id_token")
        if not id_token:
            raise UnauthorizedError("Entra response missing id_token")

        claims = await self._validate_id_token(id_token, access_token=body.get("access_token"))
        entra_oid = claims.get("oid") or claims.get("sub")
        email = (claims.get("preferred_username") or claims.get("email") or "").lower()
        full_name = claims.get("name")
        if not entra_oid or not email:
            raise UnauthorizedError("Entra token missing required claims")

        async with self._uow_factory() as uow:
            user = await uow.users.get_by_entra_oid(entra_oid)
            if not user:
                user = await uow.users.create(
                    UserRecord(
                        id=uuid.uuid4(),
                        company_id=None,
                        entra_oid=entra_oid,
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

    async def refresh(self, refresh_token: str) -> dict:
        from app.core.security import decode_token

        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")
        user_id = uuid.UUID(payload["sub"])
        async with self._uow_factory() as uow:
            user = await uow.users.get_by_id(user_id)
            if not user:
                raise UnauthorizedError("User not found")
        return self._tokens.issue_tokens(user)

    async def _validate_id_token(self, id_token: str, *, access_token: str | None = None) -> dict:
        global _JWKS_CACHE
        tenant = settings.entra_tenant_id
        issuer = f"https://login.microsoftonline.com/{tenant}/v2.0"
        jwks_uri = f"https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"

        if _JWKS_CACHE is None:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(jwks_uri)
                response.raise_for_status()
                _JWKS_CACHE = response.json()

        try:
            header = jwt.get_unverified_header(id_token)
            kid = header.get("kid")
            key = next((k for k in _JWKS_CACHE["keys"] if k["kid"] == kid), None)
            if not key:
                raise UnauthorizedError("Signing key not found")
            return jwt.decode(
                id_token,
                key,
                algorithms=["RS256"],
                audience=settings.entra_client_id,
                issuer=issuer,
                access_token=access_token,
                options={"verify_at_hash": bool(access_token)},
            )
        except JWTError as exc:
            raise UnauthorizedError("Invalid Entra id_token") from exc
