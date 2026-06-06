"""Auth API schemas."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class MockLoginRequest(BaseModel):
    email: EmailStr


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    company_id: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class MeResponse(BaseModel):
    user: UserResponse
