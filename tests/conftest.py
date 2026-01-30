"""Pytest configuration and fixtures."""

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Force test environment before importing app — os.environ[] instead of setdefault
# to ensure tests never run against the production database (setdefault would be
# silently overridden by .env values loaded via pydantic-settings).
# Use DB_HOST env var to support both Docker (db) and local (localhost:5433) runs.
_db_host = os.environ.get("DB_HOST", "localhost:5433")
os.environ["DATABASE_URL"] = (
    f"postgresql+asyncpg://groundwork:groundwork@{_db_host}/groundwork_test"
)
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "false"

from groundwork.auth import models as auth_models  # noqa: F401
from groundwork.core.config import get_settings
from groundwork.core.database import Base, get_db
from groundwork.issues import models as issues_models  # noqa: F401
from groundwork.main import create_app
from groundwork.projects import models as projects_models  # noqa: F401
from groundwork.setup import models as setup_models  # noqa: F401
from groundwork.setup.middleware import set_session_factory_override
from groundwork.setup.models import InstanceConfig

# Clear settings cache to use test settings
get_settings.cache_clear()
settings = get_settings()


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Use asyncio backend for pytest-asyncio."""
    return "asyncio"


@pytest.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine with tables."""
    engine = create_async_engine(
        str(settings.database_url),
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a session that rolls back after each test."""
    session_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(
    db_session: AsyncSession, db_engine: AsyncEngine
) -> AsyncGenerator[AsyncClient, None]:
    """Test client with overridden database dependency."""
    app = create_app()

    # Create a session factory from the test engine for middleware
    test_session_factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Insert InstanceConfig so setup middleware doesn't redirect
    async with test_session_factory() as setup_session:
        config = InstanceConfig(
            instance_name="Test Instance",
            base_url="http://test",
            setup_completed=True,
        )
        setup_session.add(config)
        await setup_session.commit()

    # Override the middleware's session factory so it reads from the test DB
    set_session_factory_override(test_session_factory)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    # Clean up the override
    set_session_factory_override(None)
