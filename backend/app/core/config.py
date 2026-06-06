"""12-factor application settings (pydantic-settings)."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
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
    database_url: str = "postgresql+asyncpg://vyaparai:vyaparai@localhost:5432/vyaparai"

    # Auth / JWT
    jwt_secret: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"

    # CORS
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # External-service toggles (mock by default for local dev)
    use_mock_llm: bool = True
    use_mock_blob: bool = True
    use_mock_whatsapp: bool = True
    use_mock_auth: bool = True

    # Azure OpenAI (used when use_mock_llm is False)
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment: str = "gpt-5"
    azure_openai_api_version: str = "2024-08-01-preview"

    # Azure Blob (used when use_mock_blob is False)
    azure_blob_connection_string: str | None = None
    azure_blob_container: str = "invoices"
    local_blob_dir: str = "local_blob_storage"

    # WhatsApp Cloud API (used when use_mock_whatsapp is False)
    whatsapp_phone_number_id: str | None = None
    whatsapp_access_token: str | None = None
    whatsapp_verify_token: str = "vyaparai-verify"
    whatsapp_app_secret: str | None = None

    # Entra ID (used when use_mock_auth is False)
    entra_tenant_id: str | None = None
    entra_client_id: str | None = None
    entra_client_secret: str | None = None

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
