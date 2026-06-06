"""Mock auth adapter for local development."""
from __future__ import annotations

from app.application.ports.repositories import UserRecord
from app.core.security import create_access_token, create_refresh_token


class MockAuthProvider:
    async def login(self, user: UserRecord) -> dict:
        access = create_access_token(
            user_id=str(user.id),
            company_id=str(user.company_id),
            role=user.role,
        )
        refresh = create_refresh_token(user_id=str(user.id))
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": 900,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "company_id": str(user.company_id),
            },
        }
