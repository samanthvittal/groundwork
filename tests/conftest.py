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
    "postgresql+asyncpg://groundwork:groundwork@localhost:5432/groundwork_test",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")

from groundwork.core.config import get_settings
from groundwork.core.database import Base, get_db
from groundwork.main import create_app

# Clear settings cache to use test settings
get_settings.cache_clear()
settings = get_settings()

# Test database engine
test_engine = create_async_engine(
    str(settings.database_url),
    echo=False,
)
test_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Use asyncio backend for pytest-asyncio."""
    return "asyncio"


@pytest.fixture(scope="session")
async def setup_database() -> AsyncGenerator[None, None]:
    """Create tables once per test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_database: None) -> AsyncGenerator[AsyncSession, None]:
    """Transaction-wrapped session that rolls back after each test."""
    async with test_engine.connect() as conn:
        await conn.begin()
        async with test_session_factory(bind=conn) as session:
            yield session
        await conn.rollback()


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
