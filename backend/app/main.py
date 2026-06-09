"""FastAPI application factory."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.middleware import RateLimitMiddleware, RequestIdMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.constants import API_V1_PREFIX, APP_NAME, HEALTH_LIVE_PATH, HEALTH_METRICS_PATH, HEALTH_READY_PATH
from app.core.metrics import metrics
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.infrastructure.db.session import engine
from app.startup.seed import seed_demo_data
from app.workers.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    if settings.environment in {"local", "dev"}:
        await seed_demo_data()
    start_scheduler()
    yield
    stop_scheduler()


def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_NAME,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{API_V1_PREFIX}/openapi.json",
        lifespan=lifespan,
    )
    register_exception_handlers(app)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=API_V1_PREFIX)

    @app.get(HEALTH_LIVE_PATH)
    async def health_live() -> dict:
        return {"status": "ok"}

    @app.get(HEALTH_READY_PATH)
    async def health_ready() -> dict:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return {"status": "ready", "database": "ok"}
        except Exception:
            return {"status": "not_ready", "database": "error"}

    @app.get(HEALTH_METRICS_PATH)
    async def health_metrics() -> dict:
        return metrics.snapshot()

    @app.get("/health/integrations")
    async def health_integrations() -> dict:
        """Non-secret integration mode summary for deploy verification."""
        return {
            "environment": settings.environment,
            "auth_mode": "mock" if settings.use_mock_auth else "oauth",
            "llm_mode": "mock" if settings.use_mock_llm else "azure_openai",
            "blob_mode": "mock" if settings.use_mock_blob else "azure",
            "whatsapp_mode": "mock" if settings.use_mock_whatsapp else "live",
            "google_oauth_configured": bool(settings.google_client_id),
            "entra_oauth_configured": bool(settings.entra_client_id),
            "azure_openai_configured": bool(
                settings.azure_openai_endpoint and settings.azure_openai_api_key
            ),
            "azure_blob_configured": bool(settings.azure_blob_connection_string),
            "whatsapp_configured": bool(
                settings.whatsapp_phone_number_id and settings.whatsapp_access_token
            ),
        }

    return app


app = create_app()
