"""Tests for user management routes."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from groundwork.auth.dependencies import get_current_user
from groundwork.core.database import get_db


@pytest.fixture
def app() -> FastAPI:
    """Create test FastAPI app with users routes."""
    from groundwork.users.routes import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/users")
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
    role.name = "admin"
    role.description = "Administrator"
    role.is_system = True
    role.permissions = []
    # Default: has all permissions
    role.has_permission = MagicMock(return_value=True)
    return role


@pytest.fixture
def mock_user(mock_role: MagicMock) -> MagicMock:
    """Create a mock authenticated user with permissions."""
    user = MagicMock()
    user.id = uuid4()
    user.email = "admin@example.com"
    user.first_name = "Admin"
    user.last_name = "User"
    user.display_name = None
    user.avatar_path = None
    user.is_active = True
    user.email_verified = True
    user.timezone = "UTC"
    user.language = "en"
    user.theme = "system"
    user.created_at = datetime(2024, 1, 1, 0, 0, 0)
    user.updated_at = datetime(2024, 1, 1, 0, 0, 0)
    user.last_login_at = None
    user.role_id = mock_role.id
    user.role = mock_role
    return user


@pytest.fixture
def mock_user_no_permission(mock_role: MagicMock) -> MagicMock:
    """Create a mock authenticated user without permissions."""
    role = MagicMock()
    role.id = uuid4()
    role.name = "viewer"
    role.has_permission = MagicMock(return_value=False)

    user = MagicMock()
    user.id = uuid4()
    user.email = "viewer@example.com"
    user.first_name = "Viewer"
    user.last_name = "User"
    user.display_name = None
    user.avatar_path = None
    user.is_active = True
    user.email_verified = True
    user.timezone = "UTC"
    user.language = "en"
    user.theme = "system"
    user.created_at = datetime(2024, 1, 1, 0, 0, 0)
    user.updated_at = datetime(2024, 1, 1, 0, 0, 0)
    user.last_login_at = None
    user.role_id = role.id
    user.role = role
    return user


@pytest.fixture
def mock_target_user(mock_role: MagicMock) -> MagicMock:
    """Create a mock user to be operated on."""
    user = MagicMock()
    user.id = uuid4()
    user.email = "target@example.com"
    user.first_name = "Target"
    user.last_name = "User"
    user.display_name = "Targeter"
    user.avatar_path = None
    user.is_active = True
    user.email_verified = False
    user.timezone = "UTC"
    user.language = "en"
    user.theme = "dark"
    user.created_at = datetime(2024, 1, 2, 0, 0, 0)
    user.updated_at = datetime(2024, 1, 2, 0, 0, 0)
    user.last_login_at = None
    user.role_id = mock_role.id
    user.role = mock_role
    return user


# =============================================================================
# GET /api/v1/users/ - List users (paginated)
# =============================================================================


@pytest.mark.asyncio
async def test_list_users_returns_paginated_list(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_target_user: MagicMock
) -> None:
    """GET /users/ should return paginated list of users."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.users.routes.UserService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.list_users.return_value = [mock_user, mock_target_user]
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/users/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    mock_service.list_users.assert_called_once_with(skip=0, limit=100)


@pytest.mark.asyncio
async def test_list_users_respects_pagination_params(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """GET /users/ should respect skip and limit params."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.users.routes.UserService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.list_users.return_value = []
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/users/?skip=10&limit=20")

    assert response.status_code == 200
    mock_service.list_users.assert_called_once_with(skip=10, limit=20)


@pytest.mark.asyncio
async def test_list_users_requires_permission(
    app: FastAPI, mock_db: AsyncMock, mock_user_no_permission: MagicMock
) -> None:
    """GET /users/ should require users:read permission."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user_no_permission

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/users/")

    assert response.status_code == 403
    assert "Permission denied" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_users_requires_authentication(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """GET /users/ should require authentication."""
    from fastapi import HTTPException, status

    app.dependency_overrides[get_db] = lambda: mock_db

    async def unauthenticated() -> None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    app.dependency_overrides[get_current_user] = unauthenticated

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/users/")

    assert response.status_code == 401


# =============================================================================
# POST /api/v1/users/ - Create user
# =============================================================================


@pytest.mark.asyncio
async def test_create_user_success(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_target_user: MagicMock
) -> None:
    """POST /users/ should create a new user."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.users.routes.UserService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.create_user.return_value = mock_target_user
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/users/",
                json={
                    "email": "target@example.com",
                    "password": "password123",
                    "first_name": "Target",
                    "last_name": "User",
                    "role_id": str(mock_target_user.role_id),
                },
            )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "target@example.com"
    assert data["first_name"] == "Target"


@pytest.mark.asyncio
async def test_create_user_validates_email(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """POST /users/ should validate email format."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/users/",
            json={
                "email": "invalid-email",
                "password": "password123",
                "first_name": "Test",
                "last_name": "User",
                "role_id": str(uuid4()),
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_validates_password_length(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """POST /users/ should validate password minimum length."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/users/",
            json={
                "email": "test@example.com",
                "password": "short",
                "first_name": "Test",
                "last_name": "User",
                "role_id": str(uuid4()),
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_requires_permission(
    app: FastAPI, mock_db: AsyncMock, mock_user_no_permission: MagicMock
) -> None:
    """POST /users/ should require users:create permission."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user_no_permission

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/users/",
            json={
                "email": "test@example.com",
                "password": "password123",
                "first_name": "Test",
                "last_name": "User",
                "role_id": str(uuid4()),
            },
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_user_duplicate_email_returns_409(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """POST /users/ should return 409 for duplicate email."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.users.routes.UserService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.create_user.return_value = None  # Email already exists
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/users/",
                json={
                    "email": "existing@example.com",
                    "password": "password123",
                    "first_name": "Test",
                    "last_name": "User",
                    "role_id": str(uuid4()),
                },
            )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


# =============================================================================
# GET /api/v1/users/{id} - Get user details
# =============================================================================


@pytest.mark.asyncio
async def test_get_user_success(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_target_user: MagicMock
) -> None:
    """GET /users/{id} should return user details."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.users.routes.UserService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_user.return_value = mock_target_user
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/users/{mock_target_user.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "target@example.com"


@pytest.mark.asyncio
async def test_get_user_not_found(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """GET /users/{id} should return 404 when user not found."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.users.routes.UserService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_user.return_value = None
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/users/{uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_user_invalid_uuid_returns_404(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """GET /users/{id} should return 404 for invalid UUID."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/users/invalid-uuid")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_user_requires_permission(
    app: FastAPI, mock_db: AsyncMock, mock_user_no_permission: MagicMock
) -> None:
    """GET /users/{id} should require users:read permission."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user_no_permission

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/api/v1/users/{uuid4()}")

    assert response.status_code == 403


# =============================================================================
# PATCH /api/v1/users/{id} - Update user
# =============================================================================


@pytest.mark.asyncio
async def test_update_user_success(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_target_user: MagicMock
) -> None:
    """PATCH /users/{id} should update user."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    # Modify the mock to reflect the update
    mock_target_user.first_name = "Updated"

    with patch("groundwork.users.routes.UserService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.update_user.return_value = mock_target_user
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/users/{mock_target_user.id}",
                json={"first_name": "Updated"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"


@pytest.mark.asyncio
async def test_update_user_not_found(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """PATCH /users/{id} should return 404 when user not found."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.users.routes.UserService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.update_user.return_value = None
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/users/{uuid4()}",
                json={"first_name": "Updated"},
            )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_user_invalid_uuid_returns_404(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """PATCH /users/{id} should return 404 for invalid UUID."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            "/api/v1/users/invalid-uuid",
            json={"first_name": "Updated"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_user_requires_permission(
    app: FastAPI, mock_db: AsyncMock, mock_user_no_permission: MagicMock
) -> None:
    """PATCH /users/{id} should require users:update permission."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user_no_permission

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            f"/api/v1/users/{uuid4()}",
            json={"first_name": "Updated"},
        )

    assert response.status_code == 403


# =============================================================================
# DELETE /api/v1/users/{id} - Deactivate user (soft delete)
# =============================================================================


@pytest.mark.asyncio
async def test_delete_user_deactivates(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_target_user: MagicMock
) -> None:
    """DELETE /users/{id} should deactivate user (soft delete)."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.users.routes.UserService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.deactivate_user.return_value = True
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/api/v1/users/{mock_target_user.id}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_user_not_found(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """DELETE /users/{id} should return 404 when user not found."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.users.routes.UserService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.deactivate_user.return_value = False
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/api/v1/users/{uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_invalid_uuid_returns_404(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """DELETE /users/{id} should return 404 for invalid UUID."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete("/api/v1/users/invalid-uuid")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_requires_permission(
    app: FastAPI, mock_db: AsyncMock, mock_user_no_permission: MagicMock
) -> None:
    """DELETE /users/{id} should require users:delete permission."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user_no_permission

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete(f"/api/v1/users/{uuid4()}")

    assert response.status_code == 403


# =============================================================================
# PUT /api/v1/users/{id}/password - Reset user password (admin)
# =============================================================================


@pytest.mark.asyncio
async def test_reset_password_success(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_target_user: MagicMock
) -> None:
    """PUT /users/{id}/password should reset user password without old password."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.users.routes.UserService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.reset_password.return_value = True
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put(
                f"/api/v1/users/{mock_target_user.id}/password",
                json={"new_password": "newpassword123"},
            )

    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successfully"


@pytest.mark.asyncio
async def test_reset_password_user_not_found(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """PUT /users/{id}/password should return 404 when user not found."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.users.routes.UserService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.reset_password.return_value = False
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put(
                f"/api/v1/users/{uuid4()}/password",
                json={"new_password": "newpassword123"},
            )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reset_password_invalid_uuid_returns_404(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """PUT /users/{id}/password should return 404 for invalid UUID."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put(
            "/api/v1/users/invalid-uuid/password",
            json={"new_password": "newpassword123"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reset_password_validates_password_length(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """PUT /users/{id}/password should validate password minimum length."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put(
            f"/api/v1/users/{uuid4()}/password",
            json={"new_password": "short"},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_reset_password_requires_permission(
    app: FastAPI, mock_db: AsyncMock, mock_user_no_permission: MagicMock
) -> None:
    """PUT /users/{id}/password should require users:update permission."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user_no_permission

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put(
            f"/api/v1/users/{uuid4()}/password",
            json={"new_password": "newpassword123"},
        )

    assert response.status_code == 403
