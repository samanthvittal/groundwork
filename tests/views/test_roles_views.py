"""Tests for role management views."""

import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from groundwork.core.database import Base, get_db
from groundwork.main import create_app
from groundwork.setup.middleware import set_session_factory_override


@pytest.fixture
async def isolated_db_session():
    """Create an isolated database session for view tests."""
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://groundwork:groundwork@localhost:5433/groundwork_test",
    )
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    set_session_factory_override(session_factory)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session, session_factory
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
    set_session_factory_override(None)


@pytest.mark.asyncio
async def test_roles_list_returns_response(isolated_db_session) -> None:
    """GET /roles should return response or redirect."""
    session, session_factory = isolated_db_session

    app = create_app()

    async def override_get_db():
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/roles", follow_redirects=False)
        # Should return 401 Unauthorized when not logged in,
        # or 307 redirect if setup is not complete
        assert response.status_code in [307, 401]
