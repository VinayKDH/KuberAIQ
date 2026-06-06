"""FastAPI application factory."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.middleware import RateLimitMiddleware, RequestIdMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.constants import API_V1_PREFIX, APP_NAME, HEALTH_LIVE_PATH, HEALTH_READY_PATH
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.infrastructure.db.session import engine
from app.startup.seed import seed_demo_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    if settings.environment == "local":
        await seed_demo_data()
    yield


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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestIdMiddleware)
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

    return app


app = create_app()
