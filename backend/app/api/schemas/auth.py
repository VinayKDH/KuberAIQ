"""Auth API schemas."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class MockLoginRequest(BaseModel):
    email: EmailStr


class EntraCallbackRequest(BaseModel):
    code: str
    code_verifier: str
    redirect_uri: str


class GoogleCallbackRequest(BaseModel):
    code: str
    code_verifier: str
    redirect_uri: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    company_id: str | None
    whatsapp_phone: str | None = None


class UpdateWhatsappPhoneRequest(BaseModel):
    phone: str | None = Field(default=None, max_length=13)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    needs_payment: bool = False
    needs_onboarding: bool = False
    user: UserResponse


class MeResponse(BaseModel):
    user: UserResponse
    needs_payment: bool = False
    needs_onboarding: bool = False
    subscription_status: str | None = None
    subscription_active: bool = False
