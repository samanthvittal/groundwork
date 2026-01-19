"""Pytest configuration and fixtures."""

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Set test environment before importing app
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://groundwork:groundwork@localhost:5433/groundwork_test",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")

from groundwork.auth import models as auth_models  # noqa: F401
from groundwork.core.config import get_settings
from groundwork.core.database import Base, get_db
from groundwork.main import create_app
from groundwork.projects import models as projects_models  # noqa: F401
from groundwork.setup import models as setup_models  # noqa: F401

# Clear settings cache to use test settings
get_settings.cache_clear()
settings = get_settings()


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Use asyncio backend for pytest-asyncio."""
    return "asyncio"


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create tables and provide a session that rolls back after each test."""
    # Create engine and session factory per test to avoid event loop issues
    engine = create_async_engine(
        str(settings.database_url),
        echo=False,
    )
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Test client with overridden database dependency."""
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
