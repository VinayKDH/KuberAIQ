"""Pytest fixtures — in-memory SQLite test DB and FastAPI client."""
from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.constants import (
    DEFAULT_INVOICE_PREFIX,
    DEMO_COMPANY_ADDRESS,
    DEMO_COMPANY_GSTIN,
    DEMO_COMPANY_NAME,
    DEMO_COMPANY_STATE,
    DEMO_USER_EMAIL,
    DEMO_USER_NAME,
)
from app.core.security import create_access_token
from app.domain.enums import UserRole
from app.infrastructure.db.base import Base
from app.infrastructure.db.models.company import CompanyModel
from app.infrastructure.db.models.user import UserModel
from app.main import create_app
from app.startup.seed import DEMO_COMPANY_ID, DEMO_USER_ID

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        company = CompanyModel(
            id=DEMO_COMPANY_ID,
            legal_name=DEMO_COMPANY_NAME,
            gstin=DEMO_COMPANY_GSTIN,
            state_code=DEMO_COMPANY_STATE,
            address=DEMO_COMPANY_ADDRESS,
            invoice_prefix=DEFAULT_INVOICE_PREFIX,
        )
        user = UserModel(
            id=DEMO_USER_ID,
            company_id=DEMO_COMPANY_ID,
            email=DEMO_USER_EMAIL,
            full_name=DEMO_USER_NAME,
            role=UserRole.OWNER,
        )
        session.add(company)
        session.add(user)
        await session.commit()
        yield session


@pytest.fixture
def auth_headers() -> dict[str, str]:
    token = create_access_token(
        user_id=str(DEMO_USER_ID),
        company_id=str(DEMO_COMPANY_ID),
        role=UserRole.OWNER,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def client(db_engine, monkeypatch) -> AsyncGenerator[AsyncClient, None]:
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        company = CompanyModel(
            id=DEMO_COMPANY_ID,
            legal_name=DEMO_COMPANY_NAME,
            gstin=DEMO_COMPANY_GSTIN,
            state_code=DEMO_COMPANY_STATE,
            address=DEMO_COMPANY_ADDRESS,
            invoice_prefix=DEFAULT_INVOICE_PREFIX,
        )
        user = UserModel(
            id=DEMO_USER_ID,
            company_id=DEMO_COMPANY_ID,
            email=DEMO_USER_EMAIL,
            full_name=DEMO_USER_NAME,
            role=UserRole.OWNER,
        )
        session.add(company)
        session.add(user)
        await session.commit()

    import app.infrastructure.db.session as session_mod
    from app.core import container as container_mod

    monkeypatch.setattr(session_mod, "AsyncSessionLocal", session_factory)
    container_mod.build_container.cache_clear()

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    container_mod.build_container.cache_clear()
