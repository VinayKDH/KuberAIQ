"""12-factor application settings (pydantic-settings)."""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Environment
    environment: Literal["local", "dev", "staging", "production"] = "local"
    debug: bool = True
    log_level: str = "INFO"

    # Database — async SQLAlchemy URL (asyncpg in prod, aiosqlite for quick local/tests)
    database_url: str = "postgresql+asyncpg://kuberaiq:kuberaiq@localhost:5432/kuberaiq"

    # Auth / JWT
    jwt_secret: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"

    # CORS — JSON array in Azure App Settings; Azure CLI may strip quotes from URLs.
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value]
        if not isinstance(value, str):
            return []
        raw = value.strip()
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            pass
        if raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1].strip()
            if not inner:
                return []
            return [part.strip() for part in inner.split(",") if part.strip()]
        return [raw]

    # External-service toggles (mock by default for local dev)
    use_mock_llm: bool = True
    use_mock_blob: bool = True
    use_mock_whatsapp: bool = True
    use_mock_auth: bool = True
    use_mock_billing: bool = True

    # Razorpay (used when use_mock_billing is False)
    razorpay_key_id: str | None = None
    razorpay_key_secret: str | None = None
    razorpay_webhook_secret: str | None = None
    subscription_plan_amount_paise: int = 99900

    # Azure OpenAI (used when use_mock_llm is False)
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-08-01-preview"

    # Azure Blob (used when use_mock_blob is False)
    azure_blob_connection_string: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "AZURE_BLOB_CONNECTION_STRING",
            "AZURE_STORAGE_CONNECTION_STRING",
            "azure_blob_connection_string",
        ),
    )
    azure_blob_container: str = Field(
        default="invoices",
        validation_alias=AliasChoices(
            "AZURE_BLOB_CONTAINER",
            "AZURE_STORAGE_CONTAINER",
            "azure_blob_container",
        ),
    )
    local_blob_dir: str = "local_blob_storage"

    # WhatsApp Cloud API (used when use_mock_whatsapp is False)
    whatsapp_phone_number_id: str | None = None
    whatsapp_access_token: str | None = None
    whatsapp_verify_token: str = "kuberaiq-verify"
    whatsapp_app_secret: str | None = None

    # Entra ID (used when use_mock_auth is False)
    entra_tenant_id: str | None = None
    entra_client_id: str | None = None
    entra_client_secret: str | None = None

    # Google OAuth (used when use_mock_auth is False)
    google_client_id: str | None = None
    google_client_secret: str | None = None

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
