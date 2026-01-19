"""Tests for project API routes."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from groundwork.auth.dependencies import get_current_user
from groundwork.core.database import get_db
from groundwork.projects.models import ProjectRole, ProjectStatus, ProjectVisibility


@pytest.fixture
def app() -> FastAPI:
    """Create test FastAPI app with projects routes."""
    from groundwork.projects.routes import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/projects")
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
    user.is_admin = False  # Not a system admin by default
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
def mock_member(mock_user: MagicMock) -> MagicMock:
    """Create a mock project member."""
    member = MagicMock()
    member.id = uuid4()
    member.project_id = uuid4()
    member.user_id = mock_user.id
    member.role = ProjectRole.OWNER
    member.joined_at = datetime(2024, 1, 1, 0, 0, 0)
    member.user = mock_user
    return member


@pytest.fixture
def mock_project(mock_user: MagicMock, mock_member: MagicMock) -> MagicMock:
    """Create a mock project."""
    project = MagicMock()
    project.id = uuid4()
    project.key = "TEST"
    project.name = "Test Project"
    project.description = "A test project"
    project.visibility = ProjectVisibility.PRIVATE
    project.status = ProjectStatus.ACTIVE
    project.owner_id = mock_user.id
    project.created_at = datetime(2024, 1, 1, 0, 0, 0)
    project.updated_at = datetime(2024, 1, 1, 0, 0, 0)
    project.archived_at = None
    project.owner = mock_user
    project.members = [mock_member]
    project.member_count = 1
    return project


# =============================================================================
# GET /api/v1/projects/ - List projects
# =============================================================================


@pytest.mark.asyncio
async def test_list_projects_returns_list(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_project: MagicMock
) -> None:
    """GET /projects/ should return list of projects."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.projects.routes.ProjectService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.list_user_projects.return_value = [mock_project]
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/projects/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["key"] == "TEST"


@pytest.mark.asyncio
async def test_list_projects_requires_authentication(
    app: FastAPI, mock_db: AsyncMock
) -> None:
    """GET /projects/ should require authentication."""
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
        response = await client.get("/api/v1/projects/")

    assert response.status_code == 401


# =============================================================================
# POST /api/v1/projects/ - Create project
# =============================================================================


@pytest.mark.asyncio
async def test_create_project_success(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_project: MagicMock
) -> None:
    """POST /projects/ should create a new project."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.projects.routes.ProjectService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.create_project.return_value = mock_project
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/projects/",
                json={
                    "key": "NEW",
                    "name": "New Project",
                    "description": "A new project",
                    "visibility": "private",
                },
            )

    assert response.status_code == 201
    data = response.json()
    assert data["key"] == "TEST"  # From mock_project


@pytest.mark.asyncio
async def test_create_project_duplicate_key(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """POST /projects/ should return 409 for duplicate key."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.projects.routes.ProjectService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.create_project.return_value = None  # Key already exists
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/projects/",
                json={
                    "key": "TEST",
                    "name": "Another Project",
                },
            )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_project_invalid_key(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """POST /projects/ should validate key format."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/projects/",
            json={
                "key": "123",  # Invalid - doesn't start with letter
                "name": "Invalid Key Project",
            },
        )

    assert response.status_code == 422


# =============================================================================
# GET /api/v1/projects/{id} - Get project by ID
# =============================================================================


@pytest.mark.asyncio
async def test_get_project_success(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_project: MagicMock
) -> None:
    """GET /projects/{id} should return project."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.projects.routes.ProjectService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_project.return_value = mock_project
        mock_service.user_can_access.return_value = True
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/projects/{mock_project.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "TEST"


@pytest.mark.asyncio
async def test_get_project_not_found(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """GET /projects/{id} should return 404 for non-existent project."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.projects.routes.ProjectService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_project.return_value = None
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/projects/{uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_project_forbidden(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_project: MagicMock
) -> None:
    """GET /projects/{id} should return 403 if user cannot access."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.projects.routes.ProjectService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_project.return_value = mock_project
        mock_service.user_can_access.return_value = False
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/projects/{mock_project.id}")

    assert response.status_code == 403


# =============================================================================
# GET /api/v1/projects/key/{key} - Get project by key
# =============================================================================


@pytest.mark.asyncio
async def test_get_project_by_key(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_project: MagicMock
) -> None:
    """GET /projects/key/{key} should return project."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.projects.routes.ProjectService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_project_by_key.return_value = mock_project
        mock_service.user_can_access.return_value = True
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/projects/key/TEST")

    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "TEST"


# =============================================================================
# PATCH /api/v1/projects/{id} - Update project
# =============================================================================


@pytest.mark.asyncio
async def test_update_project_success(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_project: MagicMock
) -> None:
    """PATCH /projects/{id} should update project."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    mock_project.name = "Updated Name"

    with patch("groundwork.projects.routes.ProjectService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_project.return_value = mock_project
        mock_service.user_can_admin.return_value = True
        mock_service.update_project.return_value = mock_project
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/projects/{mock_project.id}",
                json={"name": "Updated Name"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_update_project_forbidden(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_project: MagicMock
) -> None:
    """PATCH /projects/{id} should return 403 for non-admin."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.projects.routes.ProjectService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_project.return_value = mock_project
        mock_service.user_can_admin.return_value = False
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/projects/{mock_project.id}",
                json={"name": "Updated Name"},
            )

    assert response.status_code == 403


# =============================================================================
# DELETE /api/v1/projects/{id} - Delete project
# =============================================================================


@pytest.mark.asyncio
async def test_delete_project_success(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_project: MagicMock
) -> None:
    """DELETE /projects/{id} should soft delete project."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.projects.routes.ProjectService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_project.return_value = mock_project
        mock_service.user_is_owner.return_value = True
        mock_service.delete_project.return_value = True
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/api/v1/projects/{mock_project.id}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_project_forbidden(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_project: MagicMock
) -> None:
    """DELETE /projects/{id} should return 403 for non-owner."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.projects.routes.ProjectService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_project.return_value = mock_project
        mock_service.user_is_owner.return_value = False
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/api/v1/projects/{mock_project.id}")

    assert response.status_code == 403


# =============================================================================
# POST /api/v1/projects/{id}/archive - Archive project
# =============================================================================


@pytest.mark.asyncio
async def test_archive_project_success(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_project: MagicMock
) -> None:
    """POST /projects/{id}/archive should archive project."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    mock_project.status = ProjectStatus.ARCHIVED

    with patch("groundwork.projects.routes.ProjectService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_project.return_value = mock_project
        mock_service.user_can_admin.return_value = True
        mock_service.archive_project.return_value = mock_project
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(f"/api/v1/projects/{mock_project.id}/archive")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "archived"


# =============================================================================
# GET /api/v1/projects/{id}/members - List project members
# =============================================================================


@pytest.mark.asyncio
async def test_list_project_members(
    app: FastAPI,
    mock_db: AsyncMock,
    mock_user: MagicMock,
    mock_project: MagicMock,
    mock_member: MagicMock,
) -> None:
    """GET /projects/{id}/members should return members."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.projects.routes.ProjectService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_project.return_value = mock_project
        mock_service.user_can_access.return_value = True
        mock_service.list_project_members.return_value = [mock_member]
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/projects/{mock_project.id}/members")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1


# =============================================================================
# POST /api/v1/projects/{id}/members - Add project member
# =============================================================================


@pytest.mark.asyncio
async def test_add_project_member(
    app: FastAPI,
    mock_db: AsyncMock,
    mock_user: MagicMock,
    mock_project: MagicMock,
    mock_member: MagicMock,
) -> None:
    """POST /projects/{id}/members should add member."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    new_user_id = uuid4()
    mock_member.user_id = new_user_id
    mock_member.role = ProjectRole.MEMBER

    with patch("groundwork.projects.routes.ProjectService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_project.return_value = mock_project
        mock_service.user_can_admin.return_value = True
        mock_service.add_member.return_value = mock_member
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/projects/{mock_project.id}/members",
                json={
                    "user_id": str(new_user_id),
                    "role": "member",
                },
            )

    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == str(new_user_id)


@pytest.mark.asyncio
async def test_add_project_member_duplicate(
    app: FastAPI, mock_db: AsyncMock, mock_user: MagicMock, mock_project: MagicMock
) -> None:
    """POST /projects/{id}/members should return 409 for existing member."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.projects.routes.ProjectService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_project.return_value = mock_project
        mock_service.user_can_admin.return_value = True
        mock_service.add_member.return_value = None  # Already a member
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/projects/{mock_project.id}/members",
                json={
                    "user_id": str(mock_user.id),
                    "role": "member",
                },
            )

    assert response.status_code == 409


# =============================================================================
# PATCH /api/v1/projects/{id}/members/{user_id} - Update member role
# =============================================================================


@pytest.mark.asyncio
async def test_update_member_role(
    app: FastAPI,
    mock_db: AsyncMock,
    mock_user: MagicMock,
    mock_project: MagicMock,
    mock_member: MagicMock,
) -> None:
    """PATCH /projects/{id}/members/{user_id} should update role."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    mock_member.role = ProjectRole.ADMIN

    with patch("groundwork.projects.routes.ProjectService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_project.return_value = mock_project
        mock_service.user_can_admin.return_value = True
        mock_service.update_member_role.return_value = mock_member
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/projects/{mock_project.id}/members/{mock_member.user_id}",
                json={"role": "admin"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "admin"


# =============================================================================
# DELETE /api/v1/projects/{id}/members/{user_id} - Remove member
# =============================================================================


@pytest.mark.asyncio
async def test_remove_member(
    app: FastAPI,
    mock_db: AsyncMock,
    mock_user: MagicMock,
    mock_project: MagicMock,
    mock_member: MagicMock,
) -> None:
    """DELETE /projects/{id}/members/{user_id} should remove member."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("groundwork.projects.routes.ProjectService") as mock_service_class:
        mock_service = AsyncMock()
        mock_service.get_project.return_value = mock_project
        mock_service.user_can_admin.return_value = True
        mock_service.remove_member.return_value = True
        mock_service_class.return_value = mock_service

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(
                f"/api/v1/projects/{mock_project.id}/members/{mock_member.user_id}"
            )

    assert response.status_code == 204
