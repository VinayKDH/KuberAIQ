"""Billing API schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class CheckoutResponse(BaseModel):
    key_id: str | None = None
    order_id: str
    amount_paise: int
    currency: str = "INR"
    plan_code: str
    mock_billing: bool = False


class VerifyPaymentRequest(BaseModel):
    order_id: str
    payment_id: str
    signature: str


class SubscriptionStatusResponse(BaseModel):
    subscription_status: str
    subscription_active: bool
    needs_payment: bool
    needs_onboarding: bool
    plan_code: str
    amount_paise: int
    current_period_end: str | None = None


class MockActivateResponse(BaseModel):
    message: str = "Subscription activated"
