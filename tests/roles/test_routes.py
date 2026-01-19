"""Tests for role management routes."""

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
    """Create test FastAPI app with roles routes."""
    from groundwork.roles.routes import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/roles")
    return app


@pytest.fixture
def mock_db() -> AsyncMock:
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_permission() -> MagicMock:
    """Create a mock permission."""
    perm = MagicMock()
    perm.id = uuid4()
    perm.codename = "users:read"
    perm.description = "Read users"
    return perm


@pytest.fixture
def mock_permission_2() -> MagicMock:
    """Create a second mock permission."""
    perm = MagicMock()
    perm.id = uuid4()
    perm.codename = "users:create"
    perm.description = "Create users"
    return perm


@pytest.fixture
def mock_role(mock_permission: MagicMock) -> MagicMock:
    """Create a mock role with permissions."""
    role = MagicMock()
    role.id = uuid4()
    role.name = "admin"
    role.description = "Administrator"
    role.is_system = True
    role.permissions = [mock_permission]
    role.created_at = datetime(2024, 1, 1, 0, 0, 0)
    # Default: has all permissions (for user making requests)
    role.has_permission = MagicMock(return_value=True)
    return role


@pytest.fixture
def mock_custom_role(mock_permission: MagicMock) -> MagicMock:
    """Create a mock custom role (not system)."""
    role = MagicMock()
    role.id = uuid4()
    role.name = "custom_role"
    role.description = "A custom role"
    role.is_system = False
    role.permissions = [mock_permission]
    role.created_at = datetime(2024, 1, 2, 0, 0, 0)
    role.has_permission = MagicMock(return_value=True)
    return role


@pytest.fixture
def mock_user(mock_role: MagicMock) -> MagicMock:
    """Create a mock authenticated user with roles:manage permission."""
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


# =============================================================================
# GET /api/v1/roles/ - List all roles
# =============================================================================


@pytest.mark.asyncio
async def test_list_roles_returns_all_roles(
    app: FastAPI,
    mock_db: AsyncMock,
    mock_user: MagicMock,
    mock_role: MagicMock,
    mock_custom_role: MagicMock,
) -> None:
    """GET /roles/ should return list of all roles."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.roles.routes.RoleService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.list_roles.return_value = [mock_role, mock_custom_role]
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/roles/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    mock_service.list_roles.assert_called_once()


@pytest.mark.asyncio
async def test_list_roles_requires_permission(
    app: FastAPI, mock_db: AsyncMock, mock_user_no_permission: MagicMock
) -> None:
    """GET /roles/ should require roles:manage permission."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user_no_permission

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/roles/")

    assert response.status_code == 403
    assert "Permission denied" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_roles_requires_authentication(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """GET /roles/ should require authentication."""
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
        response = await client.get("/api/v1/roles/")

    assert response.status_code == 401


# =============================================================================
# POST /api/v1/roles/ - Create custom role
# =============================================================================


@pytest.mark.asyncio
async def test_create_role_success(
    app: FastAPI,
    mock_db: AsyncMock,
    mock_user: MagicMock,
    mock_custom_role: MagicMock,
    mock_permission: MagicMock,
) -> None:
    """POST /roles/ should create a new custom role."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.roles.routes.RoleService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.create_role.return_value = mock_custom_role
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/roles/",
                json={
                    "name": "custom_role",
                    "description": "A custom role",
                    "permission_ids": [str(mock_permission.id)],
                },
            )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "custom_role"
    assert data["is_system"] is False


@pytest.mark.asyncio
async def test_create_role_validates_name_required(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """POST /roles/ should require name field."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/roles/",
            json={
                "description": "A custom role",
                "permission_ids": [],
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_role_duplicate_name_returns_409(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """POST /roles/ should return 409 for duplicate name."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.roles.routes.RoleService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.create_role.return_value = None  # Name already exists
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/roles/",
                json={
                    "name": "admin",
                    "description": "Duplicate admin",
                    "permission_ids": [],
                },
            )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_role_requires_permission(
    app: FastAPI, mock_db: AsyncMock, mock_user_no_permission: MagicMock
) -> None:
    """POST /roles/ should require roles:manage permission."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user_no_permission

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/roles/",
            json={
                "name": "new_role",
                "description": "A new role",
                "permission_ids": [],
            },
        )

    assert response.status_code == 403


# =============================================================================
# GET /api/v1/roles/{id} - Get role details
# =============================================================================


@pytest.mark.asyncio
async def test_get_role_success(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_role: MagicMock
) -> None:
    """GET /roles/{id} should return role details with permissions."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.roles.routes.RoleService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_role.return_value = mock_role
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/roles/{mock_role.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "admin"
    assert "permissions" in data


@pytest.mark.asyncio
async def test_get_role_not_found(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """GET /roles/{id} should return 404 when role not found."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.roles.routes.RoleService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_role.return_value = None
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/roles/{uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_role_invalid_uuid_returns_404(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """GET /roles/{id} should return 404 for invalid UUID."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/roles/invalid-uuid")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_role_requires_permission(
    app: FastAPI, mock_db: AsyncMock, mock_user_no_permission: MagicMock
) -> None:
    """GET /roles/{id} should require roles:manage permission."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user_no_permission

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/api/v1/roles/{uuid4()}")

    assert response.status_code == 403


# =============================================================================
# PATCH /api/v1/roles/{id} - Update role
# =============================================================================


@pytest.mark.asyncio
async def test_update_role_success(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_custom_role: MagicMock
) -> None:
    """PATCH /roles/{id} should update role."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    # Modify the mock to reflect the update
    mock_custom_role.description = "Updated description"

    with patch("groundwork.roles.routes.RoleService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.update_role.return_value = mock_custom_role
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/roles/{mock_custom_role.id}",
                json={"description": "Updated description"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_update_role_with_permission_ids(
    app: FastAPI,
    mock_db: AsyncMock,
    mock_user: MagicMock,
    mock_custom_role: MagicMock,
    mock_permission: MagicMock,
    mock_permission_2: MagicMock,
) -> None:
    """PATCH /roles/{id} should update role permissions when permission_ids provided."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    mock_custom_role.permissions = [mock_permission, mock_permission_2]

    with patch("groundwork.roles.routes.RoleService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.update_role.return_value = mock_custom_role
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/roles/{mock_custom_role.id}",
                json={
                    "permission_ids": [
                        str(mock_permission.id),
                        str(mock_permission_2.id),
                    ]
                },
            )

    assert response.status_code == 200
    mock_service.update_role.assert_called_once()


@pytest.mark.asyncio
async def test_update_role_not_found(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """PATCH /roles/{id} should return 404 when role not found."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.roles.routes.RoleService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.update_role.return_value = None
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/roles/{uuid4()}",
                json={"description": "Updated"},
            )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_role_invalid_uuid_returns_404(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """PATCH /roles/{id} should return 404 for invalid UUID."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            "/api/v1/roles/invalid-uuid",
            json={"description": "Updated"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_role_requires_permission(
    app: FastAPI, mock_db: AsyncMock, mock_user_no_permission: MagicMock
) -> None:
    """PATCH /roles/{id} should require roles:manage permission."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user_no_permission

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.patch(
            f"/api/v1/roles/{uuid4()}",
            json={"description": "Updated"},
        )

    assert response.status_code == 403


# =============================================================================
# DELETE /api/v1/roles/{id} - Delete role (non-system only)
# =============================================================================


@pytest.mark.asyncio
async def test_delete_role_success(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_custom_role: MagicMock
) -> None:
    """DELETE /roles/{id} should delete custom (non-system) role."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.roles.routes.RoleService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.delete_role.return_value = True
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/api/v1/roles/{mock_custom_role.id}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_role_refuses_system_role(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_role: MagicMock
) -> None:
    """DELETE /roles/{id} should refuse to delete system roles."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.roles.routes.RoleService") as mock_service_class:
        mock_service = AsyncMock()
        # Service returns "system" to indicate it's a system role
        mock_service.delete_role.return_value = "system"
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/api/v1/roles/{mock_role.id}")

    assert response.status_code == 400
    assert "system role" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_role_not_found(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """DELETE /roles/{id} should return 404 when role not found."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.roles.routes.RoleService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.delete_role.return_value = False
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/api/v1/roles/{uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_role_invalid_uuid_returns_404(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """DELETE /roles/{id} should return 404 for invalid UUID."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete("/api/v1/roles/invalid-uuid")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_role_requires_permission(
    app: FastAPI, mock_db: AsyncMock, mock_user_no_permission: MagicMock
) -> None:
    """DELETE /roles/{id} should require roles:manage permission."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user_no_permission

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete(f"/api/v1/roles/{uuid4()}")

    assert response.status_code == 403


# =============================================================================
# GET /api/v1/roles/permissions - List all permissions
# =============================================================================


@pytest.mark.asyncio
async def test_list_permissions_returns_all_permissions(
    app: FastAPI,
    mock_db: AsyncMock,
    mock_user: MagicMock,
    mock_permission: MagicMock,
    mock_permission_2: MagicMock,
) -> None:
    """GET /roles/permissions should return list of all permissions."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.roles.routes.RoleService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.list_permissions.return_value = [
            mock_permission,
            mock_permission_2,
        ]
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/roles/permissions")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    mock_service.list_permissions.assert_called_once()


@pytest.mark.asyncio
async def test_list_permissions_requires_permission(
    app: FastAPI, mock_db: AsyncMock, mock_user_no_permission: MagicMock
) -> None:
    """GET /roles/permissions should require roles:manage permission."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user_no_permission

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/roles/permissions")

    assert response.status_code == 403
    assert "Permission denied" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_permissions_requires_authentication(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """GET /roles/permissions should require authentication."""
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
        response = await client.get("/api/v1/roles/permissions")

    assert response.status_code == 401
