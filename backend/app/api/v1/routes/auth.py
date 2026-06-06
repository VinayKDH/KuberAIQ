"""Auth routes."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import AuthContext, get_auth_context, get_container
from app.api.schemas.auth import MeResponse, MockLoginRequest, TokenResponse, UserResponse
from app.core.config import settings
from app.core.errors import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.container import Container

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/mock-login", response_model=TokenResponse)
async def mock_login(
    body: MockLoginRequest,
    container: Annotated[Container, Depends(get_container)],
) -> TokenResponse:
    if not settings.use_mock_auth:
        raise ForbiddenError("Mock login is disabled")
    async with container.uow_factory() as uow:
        user = await uow.users.get_by_email(body.email)
        if not user:
            raise NotFoundError(f"No user found for {body.email}")
    result = await container.auth.login(user)
    return TokenResponse(**result)


@router.get("/me", response_model=MeResponse)
async def me(
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> MeResponse:
    async with container.uow_factory() as uow:
        user = await uow.users.get_by_id(auth.user_id)
    if not user:
        raise UnauthorizedError("User not found")
    return MeResponse(
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            company_id=str(user.company_id),
        )
    )
