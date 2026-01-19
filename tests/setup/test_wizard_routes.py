"""Tests for setup wizard API routes."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from groundwork.core.database import get_db


@pytest.fixture
def app() -> FastAPI:
    """Create test FastAPI app with setup routes."""
    from groundwork.setup.routes import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/setup")
    return app


@pytest.fixture
def mock_db() -> AsyncMock:
    """Mock database session."""
    return AsyncMock()


# =============================================================================
# GET /api/v1/setup/status - Get setup status
# =============================================================================


@pytest.mark.asyncio
async def test_get_status_no_config_returns_welcome(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """GET /status should return welcome step when no InstanceConfig exists."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_setup_status.return_value = {
            "setup_completed": False,
            "current_step": "welcome",
        }
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/setup/status")

    assert response.status_code == 200
    data = response.json()
    assert data["setup_completed"] is False
    assert data["current_step"] == "welcome"


@pytest.mark.asyncio
async def test_get_status_with_instance_config_returns_admin(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """GET /status should return admin step when instance is configured but no admin."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_setup_status.return_value = {
            "setup_completed": False,
            "current_step": "admin",
        }
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/setup/status")

    assert response.status_code == 200
    data = response.json()
    assert data["setup_completed"] is False
    assert data["current_step"] == "admin"


@pytest.mark.asyncio
async def test_get_status_completed_returns_complete(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """GET /status should return complete when setup is finished."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_setup_status.return_value = {
            "setup_completed": True,
            "current_step": "complete",
        }
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/setup/status")

    assert response.status_code == 200
    data = response.json()
    assert data["setup_completed"] is True
    assert data["current_step"] == "complete"


# =============================================================================
# POST /api/v1/setup/instance - Save instance settings
# =============================================================================


@pytest.mark.asyncio
async def test_save_instance_creates_config(app: FastAPI, mock_db: AsyncMock) -> None:
    """POST /instance should create InstanceConfig with valid data."""
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_config = MagicMock()
    mock_config.id = uuid4()
    mock_config.instance_name = "My Instance"
    mock_config.base_url = "https://example.com"
    mock_config.setup_completed = False
    mock_config.smtp_configured = False
    mock_config.smtp_host = None
    mock_config.smtp_port = None
    mock_config.smtp_username = None
    mock_config.smtp_password = None
    mock_config.smtp_from_address = None
    mock_config.created_at = datetime(2024, 1, 1, 0, 0, 0)
    mock_config.updated_at = datetime(2024, 1, 1, 0, 0, 0)

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.is_setup_complete.return_value = False
        mock_service.save_instance_settings.return_value = mock_config
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/setup/instance",
                json={
                    "instance_name": "My Instance",
                    "base_url": "https://example.com",
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert data["instance_name"] == "My Instance"
    assert data["base_url"] == "https://example.com"


@pytest.mark.asyncio
async def test_save_instance_validates_url_format(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """POST /instance should reject invalid URL."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.is_setup_complete.return_value = False
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/setup/instance",
                json={
                    "instance_name": "My Instance",
                    "base_url": "not-a-valid-url",
                },
            )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_save_instance_requires_instance_name(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """POST /instance should require instance_name."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.is_setup_complete.return_value = False
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/setup/instance",
                json={
                    "base_url": "https://example.com",
                },
            )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_save_instance_forbidden_when_setup_complete(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """POST /instance should return 403 when setup is already complete."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.is_setup_complete.return_value = True
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/setup/instance",
                json={
                    "instance_name": "My Instance",
                    "base_url": "https://example.com",
                },
            )

    assert response.status_code == 403
    assert "already complete" in response.json()["detail"].lower()


# =============================================================================
# POST /api/v1/setup/admin - Create admin account
# =============================================================================


@pytest.mark.asyncio
async def test_create_admin_success(app: FastAPI, mock_db: AsyncMock) -> None:
    """POST /admin should create admin user with Admin role."""
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_user = MagicMock()
    mock_user.id = uuid4()
    mock_user.email = "admin@example.com"
    mock_user.first_name = "Admin"
    mock_user.last_name = "User"
    mock_user.display_name = None
    mock_user.avatar_path = None
    mock_user.is_active = True
    mock_user.email_verified = True
    mock_user.timezone = "UTC"
    mock_user.language = "en"
    mock_user.theme = "system"
    mock_user.role_id = uuid4()
    mock_user.created_at = datetime(2024, 1, 1, 0, 0, 0)
    mock_user.updated_at = datetime(2024, 1, 1, 0, 0, 0)
    mock_user.last_login_at = None

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.is_setup_complete.return_value = False
        mock_service.create_admin_user.return_value = mock_user
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/setup/admin",
                json={
                    "email": "admin@example.com",
                    "first_name": "Admin",
                    "last_name": "User",
                    "password": "securepassword123",
                },
            )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "admin@example.com"
    assert data["first_name"] == "Admin"


@pytest.mark.asyncio
async def test_create_admin_validates_email(app: FastAPI, mock_db: AsyncMock) -> None:
    """POST /admin should validate email format."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.is_setup_complete.return_value = False
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/setup/admin",
                json={
                    "email": "invalid-email",
                    "first_name": "Admin",
                    "last_name": "User",
                    "password": "securepassword123",
                },
            )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_admin_password_too_short(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """POST /admin should return 400 for password less than 8 characters."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.is_setup_complete.return_value = False
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/setup/admin",
                json={
                    "email": "admin@example.com",
                    "first_name": "Admin",
                    "last_name": "User",
                    "password": "short",
                },
            )

    # Per spec: Returns 400 if password too short (not 422 Pydantic validation)
    assert response.status_code == 400
    assert "password" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_admin_returns_409_when_exists(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """POST /admin should return 409 if admin user already exists."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.is_setup_complete.return_value = False
        mock_service.create_admin_user.return_value = None  # User already exists
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/setup/admin",
                json={
                    "email": "admin@example.com",
                    "first_name": "Admin",
                    "last_name": "User",
                    "password": "securepassword123",
                },
            )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_admin_forbidden_when_setup_complete(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """POST /admin should return 403 when setup is already complete."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.is_setup_complete.return_value = True
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/setup/admin",
                json={
                    "email": "admin@example.com",
                    "first_name": "Admin",
                    "last_name": "User",
                    "password": "securepassword123",
                },
            )

    assert response.status_code == 403


# =============================================================================
# POST /api/v1/setup/smtp - Configure SMTP
# =============================================================================


@pytest.mark.asyncio
async def test_configure_smtp_success(app: FastAPI, mock_db: AsyncMock) -> None:
    """POST /smtp should update InstanceConfig with SMTP settings."""
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_config = MagicMock()
    mock_config.id = uuid4()
    mock_config.instance_name = "My Instance"
    mock_config.base_url = "https://example.com"
    mock_config.setup_completed = False
    mock_config.smtp_configured = True
    mock_config.smtp_host = "smtp.example.com"
    mock_config.smtp_port = 587
    mock_config.smtp_username = "user@example.com"
    mock_config.smtp_password = "password"
    mock_config.smtp_from_address = "noreply@example.com"
    mock_config.created_at = datetime(2024, 1, 1, 0, 0, 0)
    mock_config.updated_at = datetime(2024, 1, 1, 0, 0, 0)

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.is_setup_complete.return_value = False
        mock_service.configure_smtp.return_value = mock_config
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/setup/smtp",
                json={
                    "smtp_host": "smtp.example.com",
                    "smtp_port": 587,
                    "smtp_username": "user@example.com",
                    "smtp_password": "password",
                    "smtp_from_address": "noreply@example.com",
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert data["smtp_configured"] is True
    assert data["smtp_host"] == "smtp.example.com"


@pytest.mark.asyncio
async def test_configure_smtp_optional_credentials(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """POST /smtp should allow optional username and password."""
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_config = MagicMock()
    mock_config.id = uuid4()
    mock_config.instance_name = "My Instance"
    mock_config.base_url = "https://example.com"
    mock_config.setup_completed = False
    mock_config.smtp_configured = True
    mock_config.smtp_host = "smtp.example.com"
    mock_config.smtp_port = 25
    mock_config.smtp_username = None
    mock_config.smtp_password = None
    mock_config.smtp_from_address = "noreply@example.com"
    mock_config.created_at = datetime(2024, 1, 1, 0, 0, 0)
    mock_config.updated_at = datetime(2024, 1, 1, 0, 0, 0)

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.is_setup_complete.return_value = False
        mock_service.configure_smtp.return_value = mock_config
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/setup/smtp",
                json={
                    "smtp_host": "smtp.example.com",
                    "smtp_port": 25,
                    "smtp_from_address": "noreply@example.com",
                },
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_configure_smtp_forbidden_when_setup_complete(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """POST /smtp should return 403 when setup is already complete."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.is_setup_complete.return_value = True
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/setup/smtp",
                json={
                    "smtp_host": "smtp.example.com",
                    "smtp_port": 587,
                    "smtp_from_address": "noreply@example.com",
                },
            )

    assert response.status_code == 403


# =============================================================================
# POST /api/v1/setup/skip-smtp - Skip SMTP configuration
# =============================================================================


@pytest.mark.asyncio
async def test_skip_smtp_success(app: FastAPI, mock_db: AsyncMock) -> None:
    """POST /skip-smtp should mark SMTP as skipped."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.is_setup_complete.return_value = False
        mock_service.skip_smtp.return_value = True
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/setup/skip-smtp")

    assert response.status_code == 200
    assert response.json()["message"] == "SMTP configuration skipped"


@pytest.mark.asyncio
async def test_skip_smtp_forbidden_when_setup_complete(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """POST /skip-smtp should return 403 when setup is already complete."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.is_setup_complete.return_value = True
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/setup/skip-smtp")

    assert response.status_code == 403


# =============================================================================
# POST /api/v1/setup/complete - Complete setup
# =============================================================================


@pytest.mark.asyncio
async def test_complete_setup_success(app: FastAPI, mock_db: AsyncMock) -> None:
    """POST /complete should mark setup as complete."""
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_config = MagicMock()
    mock_config.id = uuid4()
    mock_config.instance_name = "My Instance"
    mock_config.base_url = "https://example.com"
    mock_config.setup_completed = True
    mock_config.smtp_configured = False
    mock_config.smtp_host = None
    mock_config.smtp_port = None
    mock_config.smtp_username = None
    mock_config.smtp_password = None
    mock_config.smtp_from_address = None
    mock_config.created_at = datetime(2024, 1, 1, 0, 0, 0)
    mock_config.updated_at = datetime(2024, 1, 1, 0, 0, 0)

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.is_setup_complete.return_value = False
        mock_service.complete_setup.return_value = mock_config
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/setup/complete")

    assert response.status_code == 200
    data = response.json()
    assert data["setup_completed"] is True


@pytest.mark.asyncio
async def test_complete_setup_fails_without_prerequisites(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """POST /complete should return 400 if prerequisites not met."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.is_setup_complete.return_value = False
        mock_service.complete_setup.return_value = None  # Prerequisites not met
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/setup/complete")

    assert response.status_code == 400
    assert "prerequisites" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_complete_setup_forbidden_when_already_complete(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """POST /complete should return 403 when setup is already complete."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.is_setup_complete.return_value = True
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/setup/complete")

    assert response.status_code == 403


# =============================================================================
# Setup routes should NOT require authentication
# =============================================================================


@pytest.mark.asyncio
async def test_setup_routes_do_not_require_auth(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """Setup routes should be accessible without authentication."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.setup.routes.SetupService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_setup_status.return_value = {
            "setup_completed": False,
            "current_step": "welcome",
        }
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # No auth headers
            response = await client.get("/api/v1/setup/status")

    # Should not return 401
    assert response.status_code != 401
    assert response.status_code == 200
