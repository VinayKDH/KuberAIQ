"""Auth use-case orchestration."""
from __future__ import annotations

import uuid

from app.application.ports.repositories import UserRecord
from app.core.errors import UnauthorizedError
from app.core.security import decode_token
from app.application.services.billing_service import BillingService


class AuthService:
    def __init__(
        self,
        uow_factory,
        entra_provider,
        google_provider=None,
        billing_service: BillingService | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._entra = entra_provider
        self._google = google_provider
        self._billing = billing_service or BillingService(uow_factory)

    async def mock_login(self, user: UserRecord) -> dict:
        return await self._billing.build_token_response(user)

    async def entra_callback(
        self,
        *,
        code: str,
        code_verifier: str,
        redirect_uri: str,
    ) -> dict:
        raw = await self._entra.exchange_entra_code(
            code=code,
            code_verifier=code_verifier,
            redirect_uri=redirect_uri,
        )
        return await self._reissue_tokens(raw)

    async def google_callback(
        self,
        *,
        code: str,
        code_verifier: str,
        redirect_uri: str,
    ) -> dict:
        if self._google is None:
            from app.core.errors import ForbiddenError

            raise ForbiddenError("Google login is disabled in mock auth mode")
        raw = await self._google.exchange_google_code(
            code=code,
            code_verifier=code_verifier,
            redirect_uri=redirect_uri,
        )
        return await self._reissue_tokens(raw)

    async def _reissue_tokens(self, token_payload: dict) -> dict:
        user_id = uuid.UUID(token_payload["user"]["id"])
        async with self._uow_factory() as uow:
            user = await uow.users.get_by_id(user_id)
            if not user:
                raise UnauthorizedError("User not found")
        return await self._billing.build_token_response(user)

    async def refresh(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")
        user_id = uuid.UUID(payload["sub"])
        async with self._uow_factory() as uow:
            user = await uow.users.get_by_id(user_id)
            if not user:
                raise UnauthorizedError("User not found")
        return await self._billing.build_token_response(user)
