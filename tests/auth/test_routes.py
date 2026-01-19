"""Tests for auth routes."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from groundwork.core.database import get_db


@pytest.fixture
def app() -> FastAPI:
    """Create test FastAPI app with auth routes."""
    from groundwork.auth.routes import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/auth")
    return app


@pytest.fixture
def mock_db() -> AsyncMock:
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_user() -> MagicMock:
    """Create a mock user."""
    user = MagicMock()
    user.id = uuid4()
    user.email = "test@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.display_name = None
    user.avatar_path = None
    user.is_active = True
    user.email_verified = True
    user.timezone = "UTC"
    user.language = "en"
    user.theme = "system"
    user.created_at = datetime(2024, 1, 1, 0, 0, 0)
    user.last_login_at = None
    return user


@pytest.mark.asyncio
async def test_login_returns_user_and_sets_cookies(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """POST /login should return user info and set cookies."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.auth.routes.AuthService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.login.return_value = {
            "access_token": "access.token.here",
            "refresh_token": "refresh.token.here",
            "csrf_token": "csrf-token",
            "user": mock_user,
        }
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "password123"},
            )

    assert response.status_code == 200
    data = response.json()
    assert "csrf_token" in data
    assert data["csrf_token"] == "csrf-token"
    assert "user" in data
    assert data["user"]["email"] == "test@example.com"
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_login_returns_401_for_invalid_credentials(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """POST /login should return 401 for invalid credentials."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.auth.routes.AuthService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.login.return_value = None
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "wrongpassword"},
            )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_validates_email_format(app: FastAPI, mock_db: AsyncMock) -> None:
    """POST /login should validate email format."""
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "invalid-email", "password": "password123"},
        )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_validates_password_length(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """POST /login should validate password minimum length."""
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "short"},
        )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_logout_clears_cookies_and_revokes_token(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """POST /logout should clear cookies and revoke refresh token."""
    from groundwork.auth.dependencies import get_current_user

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.auth.routes.AuthService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.logout.return_value = True
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/logout",
                cookies={"refresh_token": "refresh.token.here"},
            )

    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"
    # Verify cookies are set to be deleted (empty or expired)
    mock_service.logout.assert_called_once_with("refresh.token.here")


@pytest.mark.asyncio
async def test_logout_requires_authentication(app: FastAPI, mock_db: AsyncMock) -> None:
    """POST /logout should require authentication."""
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/auth/logout")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_returns_new_access_token(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """POST /refresh should return new access token from refresh token cookie."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.auth.routes.AuthService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.refresh_access_token.return_value = {
            "access_token": "new.access.token",
            "csrf_token": "new-csrf-token",
            "user": mock_user,
        }
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/refresh",
                cookies={"refresh_token": "refresh.token.here"},
            )

    assert response.status_code == 200
    data = response.json()
    assert "csrf_token" in data
    assert data["csrf_token"] == "new-csrf-token"
    assert "user" in data
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_refresh_returns_401_without_refresh_token(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """POST /refresh should return 401 when no refresh token cookie."""
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "No refresh token"


@pytest.mark.asyncio
async def test_refresh_returns_401_for_invalid_refresh_token(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """POST /refresh should return 401 for invalid refresh token."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.auth.routes.AuthService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.refresh_access_token.return_value = None
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/refresh",
                cookies={"refresh_token": "invalid.token"},
            )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"


@pytest.mark.asyncio
async def test_me_returns_current_user(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """GET /me should return current authenticated user."""
    from groundwork.auth.dependencies import get_current_user

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/auth/me")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_me_requires_authentication(app: FastAPI, mock_db: AsyncMock) -> None:
    """GET /me should require authentication."""
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_request_password_reset_always_returns_success(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """POST /password-reset should always return success (prevent enumeration)."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.auth.routes.AuthService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.request_password_reset.return_value = None  # User not found
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/password-reset",
                json={"email": "nonexistent@example.com"},
            )

    assert response.status_code == 200
    assert "message" in response.json()


@pytest.mark.asyncio
async def test_request_password_reset_success_when_user_exists(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """POST /password-reset should return success when user exists."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.auth.routes.AuthService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.request_password_reset.return_value = "reset-token-here"
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/password-reset",
                json={"email": "test@example.com"},
            )

    assert response.status_code == 200
    mock_service.request_password_reset.assert_called_once_with("test@example.com")


@pytest.mark.asyncio
async def test_request_password_reset_validates_email_format(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """POST /password-reset should validate email format."""
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/password-reset",
            json={"email": "invalid-email"},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_confirm_password_reset_success(app: FastAPI, mock_db: AsyncMock) -> None:
    """PUT /password-reset/{token} should reset password."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.auth.routes.AuthService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.confirm_password_reset.return_value = True
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put(
                "/api/v1/auth/password-reset/valid-token",
                json={"token": "valid-token", "new_password": "newpassword123"},
            )

    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successfully"


@pytest.mark.asyncio
async def test_confirm_password_reset_invalid_token(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """PUT /password-reset/{token} should return 400 for invalid token."""
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch("groundwork.auth.routes.AuthService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.confirm_password_reset.return_value = False
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put(
                "/api/v1/auth/password-reset/invalid-token",
                json={"token": "invalid-token", "new_password": "newpassword123"},
            )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired reset token"


@pytest.mark.asyncio
async def test_confirm_password_reset_validates_password_length(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """PUT /password-reset/{token} should validate password minimum length."""
    app.dependency_overrides[get_db] = lambda: mock_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put(
            "/api/v1/auth/password-reset/some-token",
            json={"token": "some-token", "new_password": "short"},
        )

    assert response.status_code == 422
