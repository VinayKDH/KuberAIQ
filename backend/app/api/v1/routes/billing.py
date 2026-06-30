"""Billing routes — subscription checkout before onboarding."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.api.deps import AuthContext, get_auth_context, get_container, get_verified_auth_context
from app.core.errors import ForbiddenError
from app.domain.enums import UserRole
from app.api.schemas.auth import TokenResponse
from app.api.schemas.billing import (
    CheckoutResponse,
    MockActivateResponse,
    SubscriptionStatusResponse,
    VerifyPaymentRequest,
)
from app.core.config import settings
from app.core.container import Container

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/status", response_model=SubscriptionStatusResponse)
async def subscription_status(
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> SubscriptionStatusResponse:
    data = await container.billing_service.get_status(auth.user_id)
    return SubscriptionStatusResponse(**data)


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    auth: Annotated[AuthContext, Depends(get_verified_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> CheckoutResponse:
    if auth.role != UserRole.OWNER:
        raise ForbiddenError("Only the business owner can manage billing")
    if settings.use_mock_billing:
        sub = await container.billing_service.ensure_subscription(auth.user_id)
        return CheckoutResponse(
            order_id=f"mock-{auth.user_id}",
            amount_paise=sub.amount_paise,
            plan_code=sub.plan_code,
            mock_billing=True,
        )
    data = await container.billing_service.create_checkout(auth.user_id)
    return CheckoutResponse(**data, mock_billing=False)


@router.post("/verify", response_model=TokenResponse)
async def verify_payment(
    body: VerifyPaymentRequest,
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> TokenResponse:
    result = await container.billing_service.verify_payment(
        auth.user_id,
        order_id=body.order_id,
        payment_id=body.payment_id,
        signature=body.signature,
    )
    return TokenResponse(**result)


@router.post("/mock-activate", response_model=TokenResponse)
async def mock_activate(
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    container: Annotated[Container, Depends(get_container)],
) -> TokenResponse:
    result = await container.billing_service.mock_activate(auth.user_id)
    return TokenResponse(**result)


@router.post("/webhooks/razorpay", status_code=204, response_class=Response)
async def razorpay_webhook(
    request: Request,
    container: Annotated[Container, Depends(get_container)],
) -> Response:
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    await container.billing_service.handle_webhook(body, signature)
    await container.payment_service.handle_razorpay_invoice_webhook(body, signature)
    return Response(status_code=204)
