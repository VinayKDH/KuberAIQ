"""Auth routes."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.deps import AuthContext, get_tenant_context, get_verified_auth_context, get_container
from app.api.schemas.auth import (
    EntraCallbackRequest,
    GoogleCallbackRequest,
    MeResponse,
    MockLoginRequest,
    RefreshRequest,
    TokenResponse,
    UpdateWhatsappPhoneRequest,
    UserResponse,
)
from app.domain.value_objects.phone import Phone
from app.domain.exceptions import InvalidPhone
from app.application.ports.repositories import UserRecord
from app.core.config import settings
from app.core.constants import CA_EMAIL_DOMAIN, DEMO_USER_EMAIL, LEGACY_DEMO_USER_EMAIL
from app.core.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationAppError
from app.core.container import Container
from app.domain.enums import UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_response(user) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        company_id=str(user.company_id) if user.company_id else None,
        whatsapp_phone=user.whatsapp_phone,
    )


@router.post("/mock-login", response_model=TokenResponse)
async def mock_login(
    body: MockLoginRequest,
    container: Annotated[Container, Depends(get_container)],
) -> TokenResponse:
    if not settings.use_mock_auth:
        raise ForbiddenError("Mock login is disabled")
    async with container.uow_factory() as uow:
        user = await uow.users.get_by_email(body.email)
        if not user and body.email.lower() == DEMO_USER_EMAIL.lower():
            user = await uow.users.get_by_email(LEGACY_DEMO_USER_EMAIL)
        if not user:
            email = body.email.strip().lower()
            _, _, domain = email.partition("@")
            if domain.endswith("test.kuberaiq.com"):
                local_part = email.split("@", 1)[0]
                user = await uow.users.create(
                    UserRecord(
                        id=uuid.uuid4(),
                        company_id=None,
                        email=email,
                        full_name=local_part.replace("+", " ").replace(".", " ").title() or "Test User",
                        role=UserRole.OWNER,
                    )
                )
            elif email.endswith(CA_EMAIL_DOMAIN):
                local_part = email.split("@", 1)[0]
                user = await uow.users.create(
                    UserRecord(
                        id=uuid.uuid4(),
                        company_id=None,
                        email=email,
                        full_name=local_part.replace(".", " ").title() or "CA User",
                        role=UserRole.CA,
                    )
                )
            else:
                raise NotFoundError(f"No user found for {body.email}")
            await uow.commit()
    result = await container.billing_service.build_token_response(user)
    return TokenResponse(**result)


@router.post("/callback", response_model=TokenResponse)
async def entra_callback(
    body: EntraCallbackRequest,
    container: Annotated[Container, Depends(get_container)],
) -> TokenResponse:
    if settings.use_mock_auth:
        raise ForbiddenError("Entra login is disabled in mock auth mode")
    result = await container.auth_service.entra_callback(
        code=body.code,
        code_verifier=body.code_verifier,
        redirect_uri=body.redirect_uri,
    )
    return TokenResponse(**result)


@router.post("/google/callback", response_model=TokenResponse)
async def google_callback(
    body: GoogleCallbackRequest,
    container: Annotated[Container, Depends(get_container)],
) -> TokenResponse:
    if settings.use_mock_auth:
        raise ForbiddenError("Google login is disabled in mock auth mode")
    result = await container.auth_service.google_callback(
        code=body.code,
        code_verifier=body.code_verifier,
        redirect_uri=body.redirect_uri,
    )
    return TokenResponse(**result)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    body: RefreshRequest,
    container: Annotated[Container, Depends(get_container)],
) -> TokenResponse:
    result = await container.auth_service.refresh(body.refresh_token)
    return TokenResponse(**result)


@router.post("/logout", status_code=204, response_class=Response)
async def logout() -> Response:
    return Response(status_code=204)


@router.get("/me", response_model=MeResponse)
async def me(
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> MeResponse:
    async with container.uow_factory() as uow:
        user = await uow.users.get_by_id(auth.user_id)
    if not user:
        raise UnauthorizedError("User not found")
    billing = await container.billing_service.get_status(auth.user_id)
    return MeResponse(
        user=_user_response(user),
        needs_payment=billing["needs_payment"],
        needs_onboarding=billing["needs_onboarding"],
        subscription_status=billing["subscription_status"],
        subscription_active=billing["subscription_active"],
    )


@router.patch("/me/whatsapp-phone", response_model=UserResponse)
async def update_whatsapp_phone(
    body: UpdateWhatsappPhoneRequest,
    auth: Annotated[AuthContext, Depends(get_tenant_context)],
    container: Annotated[Container, Depends(get_container)],
) -> UserResponse:
    if auth.role != UserRole.OWNER:
        raise ForbiddenError("Only the business owner can link WhatsApp copilot")

    normalized: str | None = None
    if body.phone:
        try:
            normalized = Phone(body.phone.strip()).value
        except InvalidPhone as exc:
            raise ValidationAppError(str(exc)) from exc

    async with container.uow_factory() as uow:
        if normalized:
            existing = await uow.users.find_owner_by_whatsapp_phone(normalized)
            if existing and existing.id != auth.user_id:
                raise ConflictError("This WhatsApp number is linked to another KuberAIQ account")
        user = await uow.users.update_whatsapp_phone(auth.user_id, normalized)
        await uow.commit()
    return _user_response(user)
