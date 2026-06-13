"""Shared JWT session token issuance."""
from __future__ import annotations

from app.application.ports.repositories import UserRecord
from app.core.constants import ACCESS_TOKEN_TTL_MINUTES
from app.core.security import create_access_token, create_refresh_token
from app.domain.enums import UserRole


class TokenService:
    def issue_tokens(self, user: UserRecord, *, subscription_active: bool = True) -> dict:
        is_ca = user.role == UserRole.CA
        company_id = str(user.company_id) if user.company_id else None
        needs_payment = False if is_ca else not subscription_active
        needs_onboarding = False if is_ca else (subscription_active and user.company_id is None)
        access = create_access_token(
            user_id=str(user.id),
            company_id=company_id,
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
        )
        refresh = create_refresh_token(user_id=str(user.id))
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_TTL_MINUTES * 60,
            "needs_payment": needs_payment,
            "needs_onboarding": needs_onboarding,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value if hasattr(user.role, "value") else str(user.role),
                "company_id": company_id,
            },
        }
