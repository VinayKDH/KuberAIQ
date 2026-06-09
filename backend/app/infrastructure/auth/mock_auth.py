"""Mock auth adapter for local development."""
from __future__ import annotations

from app.application.ports.repositories import UserRecord
from app.core.errors import ValidationAppError
from app.infrastructure.auth.token_service import TokenService


class MockAuthProvider:
    def __init__(self, tokens: TokenService | None = None) -> None:
        self._tokens = tokens or TokenService()

    async def login(self, user: UserRecord) -> dict:
        return self._tokens.issue_tokens(user)

    async def exchange_entra_code(self, **_: object) -> dict:
        raise ValidationAppError("Entra login is disabled in mock auth mode")

    async def exchange_google_code(self, **_: object) -> dict:
        raise ValidationAppError("Google login is disabled in mock auth mode")
