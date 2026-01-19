"""Tests for profile routes."""

from datetime import datetime
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from groundwork.auth.dependencies import get_current_user
from groundwork.core.database import get_db


@pytest.fixture
def app() -> FastAPI:
    """Create test FastAPI app with profile routes."""
    from groundwork.profile.routes import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/profile")
    return app


@pytest.fixture
def mock_db() -> AsyncMock:
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_role() -> MagicMock:
    """Create a mock role with permissions."""
    role = MagicMock()
    role.id = uuid4()
    role.name = "user"
    role.description = "Regular user"
    role.is_system = False
    role.permissions = []
    role.has_permission = MagicMock(return_value=False)
    return role


@pytest.fixture
def mock_user(mock_role: MagicMock) -> MagicMock:
    """Create a mock authenticated user."""
    user = MagicMock()
    user.id = uuid4()
    user.email = "testuser@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.display_name = "TestDisplay"
    user.avatar_path = None
    user.is_active = True
    user.email_verified = True
    user.timezone = "UTC"
    user.language = "en"
    user.theme = "system"
    user.hashed_password = "hashed_password_here"
    user.created_at = datetime(2024, 1, 1, 0, 0, 0)
    user.updated_at = datetime(2024, 1, 1, 0, 0, 0)
    user.last_login_at = None
    user.role_id = mock_role.id
    user.role = mock_role
    return user


# =============================================================================
# GET /api/v1/profile/ - Get own profile
# =============================================================================


@pytest.mark.asyncio
async def test_get_profile_returns_current_user(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """GET /profile/ should return current user's profile."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/profile/")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"
    assert data["display_name"] == "TestDisplay"
    assert data["timezone"] == "UTC"
    assert data["language"] == "en"
    assert data["theme"] == "system"


@pytest.mark.asyncio
async def test_get_profile_requires_authentication(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """GET /profile/ should require authentication."""
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/profile/")

    assert response.status_code == 401


# =============================================================================
# PATCH /api/v1/profile/ - Update own profile
# =============================================================================


@pytest.mark.asyncio
async def test_update_profile_success(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """PATCH /profile/ should update profile fields."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    # Update mock to reflect changes
    mock_user.first_name = "Updated"
    mock_user.last_name = "Name"
    mock_user.display_name = "NewDisplay"

    with patch("groundwork.profile.routes.ProfileService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.update_profile.return_value = mock_user
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                "/api/v1/profile/",
                json={
                    "first_name": "Updated",
                    "last_name": "Name",
                    "display_name": "NewDisplay",
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["last_name"] == "Name"
    assert data["display_name"] == "NewDisplay"


@pytest.mark.asyncio
async def test_update_profile_partial_update(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """PATCH /profile/ should allow partial updates."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    mock_user.first_name = "OnlyFirst"

    with patch("groundwork.profile.routes.ProfileService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.update_profile.return_value = mock_user
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                "/api/v1/profile/",
                json={"first_name": "OnlyFirst"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "OnlyFirst"


@pytest.mark.asyncio
async def test_update_profile_validates_first_name_length(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """PATCH /profile/ should validate first_name max length."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            "/api/v1/profile/",
            json={"first_name": "a" * 101},  # 101 chars, max is 100
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_profile_requires_authentication(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """PATCH /profile/ should require authentication."""
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            "/api/v1/profile/",
            json={"first_name": "Updated"},
        )

    assert response.status_code == 401


# =============================================================================
# PUT /api/v1/profile/password - Change own password
# =============================================================================


@pytest.mark.asyncio
async def test_change_password_success(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """PUT /profile/password should change password when current password is correct."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.profile.routes.ProfileService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.change_password.return_value = True
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put(
                "/api/v1/profile/password",
                json={
                    "current_password": "oldpassword123",
                    "new_password": "newpassword123",
                },
            )

    assert response.status_code == 200
    assert response.json()["message"] == "Password changed successfully"


@pytest.mark.asyncio
async def test_change_password_wrong_current_password(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """PUT /profile/password should return 400 when current password is wrong."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.profile.routes.ProfileService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.change_password.return_value = False
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put(
                "/api/v1/profile/password",
                json={
                    "current_password": "wrongpassword",
                    "new_password": "newpassword123",
                },
            )

    assert response.status_code == 400
    assert response.json()["detail"] == "Current password is incorrect"


@pytest.mark.asyncio
async def test_change_password_validates_new_password_length(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """PUT /profile/password should validate new password minimum length."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put(
            "/api/v1/profile/password",
            json={
                "current_password": "oldpassword123",
                "new_password": "short",
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_change_password_requires_authentication(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """PUT /profile/password should require authentication."""
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put(
            "/api/v1/profile/password",
            json={
                "current_password": "oldpassword123",
                "new_password": "newpassword123",
            },
        )

    assert response.status_code == 401


# =============================================================================
# PUT /api/v1/profile/avatar - Upload avatar
# =============================================================================


@pytest.mark.asyncio
async def test_upload_avatar_success(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """PUT /profile/avatar should upload and save avatar."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    mock_user.avatar_path = f"uploads/avatars/{mock_user.id}.png"

    with patch("groundwork.profile.routes.ProfileService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.upload_avatar.return_value = f"uploads/avatars/{mock_user.id}.png"
        mock_service_class.return_value = mock_service

        # Create a simple PNG file content
        file_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put(
                "/api/v1/profile/avatar",
                files={"file": ("avatar.png", BytesIO(file_content), "image/png")},
            )

    assert response.status_code == 200
    data = response.json()
    assert "avatar_path" in data
    assert str(mock_user.id) in data["avatar_path"]


@pytest.mark.asyncio
async def test_upload_avatar_requires_authentication(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """PUT /profile/avatar should require authentication."""
    app.dependency_overrides[get_db] = lambda: mock_db

    file_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put(
            "/api/v1/profile/avatar",
            files={"file": ("avatar.png", BytesIO(file_content), "image/png")},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_avatar_rejects_invalid_file_type(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """PUT /profile/avatar should reject non-image file types."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.profile.routes.ProfileService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.upload_avatar.return_value = None  # Indicates rejection
        mock_service_class.return_value = mock_service

        file_content = b"not an image"

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put(
                "/api/v1/profile/avatar",
                files={"file": ("document.txt", BytesIO(file_content), "text/plain")},
            )

    assert response.status_code == 400


# =============================================================================
# GET /api/v1/profile/settings - Get user preferences
# =============================================================================


@pytest.mark.asyncio
async def test_get_settings_returns_preferences(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """GET /profile/settings should return user preferences."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/profile/settings")

    assert response.status_code == 200
    data = response.json()
    assert data["timezone"] == "UTC"
    assert data["language"] == "en"
    assert data["theme"] == "system"


@pytest.mark.asyncio
async def test_get_settings_requires_authentication(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """GET /profile/settings should require authentication."""
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/profile/settings")

    assert response.status_code == 401


# =============================================================================
# PATCH /api/v1/profile/settings - Update user preferences
# =============================================================================


@pytest.mark.asyncio
async def test_update_settings_success(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """PATCH /profile/settings should update user preferences."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    mock_user.timezone = "America/New_York"
    mock_user.language = "es"
    mock_user.theme = "dark"

    with patch("groundwork.profile.routes.ProfileService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.update_settings.return_value = mock_user
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                "/api/v1/profile/settings",
                json={
                    "timezone": "America/New_York",
                    "language": "es",
                    "theme": "dark",
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert data["timezone"] == "America/New_York"
    assert data["language"] == "es"
    assert data["theme"] == "dark"


@pytest.mark.asyncio
async def test_update_settings_partial_update(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """PATCH /profile/settings should allow partial updates."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    mock_user.theme = "dark"

    with patch("groundwork.profile.routes.ProfileService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.update_settings.return_value = mock_user
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                "/api/v1/profile/settings",
                json={"theme": "dark"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "dark"


@pytest.mark.asyncio
async def test_update_settings_validates_theme_values(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """PATCH /profile/settings should validate theme values."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            "/api/v1/profile/settings",
            json={"theme": "invalid_theme_that_is_too_long"},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_settings_requires_authentication(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """PATCH /profile/settings should require authentication."""
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            "/api/v1/profile/settings",
            json={"theme": "dark"},
        )

    assert response.status_code == 401
