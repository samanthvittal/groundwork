"""Tests for main application."""

import os
import sys

# Set required environment variables BEFORE any imports that could trigger Settings
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def clear_main_module():
    """Clear main module from cache between tests."""
    # Remove groundwork.main from sys.modules so each test gets fresh import
    yield
    if "groundwork.main" in sys.modules:
        del sys.modules["groundwork.main"]


@pytest.mark.asyncio
async def test_create_app_returns_fastapi_instance() -> None:
    """create_app should return a FastAPI application."""
    from fastapi import FastAPI

    from groundwork.main import create_app

    app = create_app()

    assert isinstance(app, FastAPI)
    assert app.title == "Groundwork"


@pytest.mark.asyncio
async def test_health_live_endpoint_accessible() -> None:
    """Health live endpoint should be accessible."""
    from groundwork.main import create_app

    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/health/live")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_request_id_middleware_adds_header() -> None:
    """Request ID middleware should add X-Request-ID header."""
    from groundwork.main import create_app

    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/health/live")

    assert "x-request-id" in response.headers
