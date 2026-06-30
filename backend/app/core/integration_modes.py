"""Integration mode helpers for health checks and deploy verification."""
from __future__ import annotations

from app.core.config import settings


def llm_mode() -> str:
    """Return ``mock`` or ``live`` for health/integrations endpoints."""
    if settings.use_mock_llm:
        return "mock"
    if settings.azure_openai_endpoint and settings.azure_openai_api_key:
        return "live"
    return "mock"


def whatsapp_mode() -> str:
    if settings.use_mock_whatsapp:
        return "mock"
    if settings.whatsapp_phone_number_id and settings.whatsapp_access_token:
        return "live"
    return "mock"


def billing_mode() -> str:
    return "mock" if settings.use_mock_billing else "razorpay"


def integration_health() -> dict:
    """Non-secret integration summary — shared by /health/integrations and admin."""
    return {
        "environment": settings.environment,
        "auth_mode": "mock" if settings.use_mock_auth else "oauth",
        "llm_mode": llm_mode(),
        "blob_mode": "mock" if settings.use_mock_blob else "azure",
        "whatsapp_mode": whatsapp_mode(),
        "billing_mode": billing_mode(),
        "google_oauth_configured": bool(settings.google_client_id),
        "entra_oauth_configured": bool(settings.entra_client_id),
        "azure_openai_configured": bool(
            settings.azure_openai_endpoint and settings.azure_openai_api_key
        ),
        "azure_blob_configured": bool(settings.azure_blob_connection_string),
        "whatsapp_configured": bool(
            settings.whatsapp_phone_number_id and settings.whatsapp_access_token
        ),
        "whatsapp_app_secret_configured": bool(settings.whatsapp_app_secret),
        "razorpay_configured": bool(settings.razorpay_key_id and settings.razorpay_key_secret),
        "razorpay_webhook_configured": bool(settings.razorpay_webhook_secret),
    }
