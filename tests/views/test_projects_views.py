"""Tests for project management views."""

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
async def test_projects_list_returns_response(isolated_db_session) -> None:
    """GET /projects should return response or redirect."""
    session, session_factory = isolated_db_session

    app = create_app()

    async def override_get_db():
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/projects", follow_redirects=False)
        # Should return 401 Unauthorized when not logged in,
        # or 307 redirect if setup is not complete
        assert response.status_code in [307, 401]


@pytest.mark.asyncio
async def test_projects_create_form_returns_response(isolated_db_session) -> None:
    """GET /projects/create should return response or redirect."""
    session, session_factory = isolated_db_session

    app = create_app()

    async def override_get_db():
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/projects/create", follow_redirects=False)
        # Should return 401 Unauthorized when not logged in,
        # or 307 redirect if setup is not complete
        assert response.status_code in [307, 401]


@pytest.mark.asyncio
async def test_projects_detail_returns_response(isolated_db_session) -> None:
    """GET /projects/{id} should return response or redirect."""
    session, session_factory = isolated_db_session

    app = create_app()

    async def override_get_db():
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db

    # Use a fake UUID for the test
    fake_uuid = "00000000-0000-0000-0000-000000000001"

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/projects/{fake_uuid}", follow_redirects=False)
        # Should return 401 Unauthorized when not logged in,
        # or 307 redirect if setup is not complete
        assert response.status_code in [307, 401]


@pytest.mark.asyncio
async def test_projects_edit_form_returns_response(isolated_db_session) -> None:
    """GET /projects/{id}/edit should return response or redirect."""
    session, session_factory = isolated_db_session

    app = create_app()

    async def override_get_db():
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db

    fake_uuid = "00000000-0000-0000-0000-000000000001"

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/projects/{fake_uuid}/edit", follow_redirects=False)
        # Should return 401 Unauthorized when not logged in,
        # or 307 redirect if setup is not complete
        assert response.status_code in [307, 401]


@pytest.mark.asyncio
async def test_projects_members_returns_response(isolated_db_session) -> None:
    """GET /projects/{id}/members should return response or redirect."""
    session, session_factory = isolated_db_session

    app = create_app()

    async def override_get_db():
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db

    fake_uuid = "00000000-0000-0000-0000-000000000001"

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            f"/projects/{fake_uuid}/members", follow_redirects=False
        )
        # Should return 401 Unauthorized when not logged in,
        # or 307 redirect if setup is not complete
        assert response.status_code in [307, 401]


@pytest.mark.asyncio
async def test_projects_delete_requires_auth(isolated_db_session) -> None:
    """POST /projects/{id}/delete should require authentication."""
    session, session_factory = isolated_db_session

    app = create_app()

    async def override_get_db():
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db

    fake_uuid = "00000000-0000-0000-0000-000000000001"

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/projects/{fake_uuid}/delete", follow_redirects=False
        )
        # Should return 401 Unauthorized when not logged in,
        # or 307 redirect if setup is not complete
        assert response.status_code in [307, 401]


@pytest.mark.asyncio
async def test_projects_create_submit_requires_auth(isolated_db_session) -> None:
    """POST /projects/create should require authentication."""
    session, session_factory = isolated_db_session

    app = create_app()

    async def override_get_db():
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/projects/create",
            data={"key": "TEST", "name": "Test Project"},
            follow_redirects=False,
        )
        # Should return 401 Unauthorized when not logged in,
        # or 307 redirect if setup is not complete
        assert response.status_code in [307, 401]


@pytest.mark.asyncio
async def test_projects_members_add_requires_auth(isolated_db_session) -> None:
    """POST /projects/{id}/members/add should require authentication."""
    session, session_factory = isolated_db_session

    app = create_app()

    async def override_get_db():
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db

    fake_uuid = "00000000-0000-0000-0000-000000000001"
    fake_user_uuid = "00000000-0000-0000-0000-000000000002"

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/projects/{fake_uuid}/members/add",
            data={"user_id": fake_user_uuid, "role": "member"},
            follow_redirects=False,
        )
        # Should return 401 Unauthorized when not logged in,
        # or 307 redirect if setup is not complete
        assert response.status_code in [307, 401]
