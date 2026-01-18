"""Tests for health routes."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from groundwork.core.database import get_db
from groundwork.health.routes import router


@pytest.fixture
def app() -> FastAPI:
    """Create FastAPI app with health router."""
    app = FastAPI()
    app.include_router(router, prefix="/health")
    return app


@pytest.fixture
def mock_db_success() -> AsyncMock:
    """Mock database session that succeeds."""
    mock = AsyncMock()
    mock.execute = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def mock_db_failure() -> AsyncMock:
    """Mock database session that fails."""
    mock = AsyncMock()
    mock.execute = AsyncMock(side_effect=Exception("Database connection failed"))
    return mock


@pytest.fixture
def mock_settings() -> MagicMock:
    """Mock settings."""
    mock = MagicMock()
    mock.environment = "test"
    return mock


@pytest.mark.asyncio
async def test_liveness_returns_ok(app: FastAPI) -> None:
    """GET /health/live should return status ok."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_readiness_returns_ok_when_db_healthy(
    app: FastAPI, mock_db_success: AsyncMock, mock_settings: MagicMock
) -> None:
    """GET /health/ready should return status ok when database is healthy."""
    app.dependency_overrides[get_db] = lambda: mock_db_success

    with patch("groundwork.health.services.get_settings", return_value=mock_settings):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_readiness_returns_503_when_db_unhealthy(
    app: FastAPI, mock_db_failure: AsyncMock, mock_settings: MagicMock
) -> None:
    """GET /health/ready should return 503 when database is unhealthy."""
    app.dependency_overrides[get_db] = lambda: mock_db_failure

    with patch("groundwork.health.services.get_settings", return_value=mock_settings):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}


@pytest.mark.asyncio
async def test_details_returns_healthy_details(
    app: FastAPI, mock_db_success: AsyncMock, mock_settings: MagicMock
) -> None:
    """GET /health/details should return detailed health info when db is healthy."""
    app.dependency_overrides[get_db] = lambda: mock_db_success

    with patch("groundwork.health.services.get_settings", return_value=mock_settings):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health/details")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert data["environment"] == "test"
    assert data["components"]["database"]["status"] == "ok"


@pytest.mark.asyncio
async def test_details_returns_degraded_when_db_unhealthy(
    app: FastAPI, mock_db_failure: AsyncMock, mock_settings: MagicMock
) -> None:
    """GET /health/details should return degraded status when db is unhealthy."""
    app.dependency_overrides[get_db] = lambda: mock_db_failure

    with patch("groundwork.health.services.get_settings", return_value=mock_settings):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health/details")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["components"]["database"]["status"] == "unavailable"
