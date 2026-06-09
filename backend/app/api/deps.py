"""FastAPI dependencies — auth, services, RBAC."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.constants import AUTH_SCHEME
from app.core.container import Container, build_container
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.domain.enums import UserRole

_bearer = HTTPBearer(auto_error=False)


@dataclass
class AuthContext:
    user_id: uuid.UUID
    company_id: uuid.UUID | None
    role: UserRole


def get_container() -> Container:
    return build_container()


async def get_auth_context(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AuthContext:
    if credentials is None or credentials.scheme.lower() != AUTH_SCHEME.lower():
        raise UnauthorizedError("Missing or invalid authorization header")
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")
    company_raw = payload.get("company_id")
    return AuthContext(
        user_id=uuid.UUID(payload["sub"]),
        company_id=uuid.UUID(company_raw) if company_raw else None,
        role=UserRole(payload["role"]),
    )


async def get_verified_auth_context(
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> AuthContext:
    """Reconcile JWT with database — prevents stale or cross-tenant token reuse."""
    async with container.uow_factory() as uow:
        user = await uow.users.get_by_id(auth.user_id)
        if not user:
            raise UnauthorizedError("User not found")
        if auth.company_id != user.company_id:
            raise UnauthorizedError("Session expired — please sign in again")
    return auth


async def get_subscribed_context(
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> AuthContext:
    if not await container.billing_service.is_active(auth.user_id):
        raise ForbiddenError("Subscription payment required before setup")
    return auth


async def get_tenant_context(
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
) -> AuthContext:
    if auth.company_id is None:
        raise ForbiddenError("Complete company onboarding first")
    return auth


def require_roles(*roles: UserRole):
    async def _check(auth: Annotated[AuthContext, Depends(get_tenant_context)]) -> AuthContext:
        if auth.role != UserRole.OWNER and auth.role not in roles:
            raise ForbiddenError("Insufficient permissions")
        return auth

    return _check


def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
