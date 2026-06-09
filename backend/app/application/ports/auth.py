"""Authentication port."""
from __future__ import annotations

from typing import Protocol

from app.application.ports.repositories import UserRecord


class AuthPort(Protocol):
    async def login(self, user: UserRecord) -> dict: ...

    async def exchange_entra_code(
        self,
        *,
        code: str,
        code_verifier: str,
        redirect_uri: str,
    ) -> dict: ...

    async def refresh(self, refresh_token: str) -> dict: ...
