"""Tests for issue API routes."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.models import Permission, Role, User
from groundwork.auth.services import AuthService
from groundwork.auth.utils import hash_password
from groundwork.issues.models import IssueType, Priority, Status, StatusCategory
from groundwork.issues.services import IssueService
from groundwork.projects.services import ProjectService


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def test_role(db_session: AsyncSession) -> Role:
    """Create a test role."""
    permission = Permission(codename="issues:read", description="Can read issues")
    db_session.add(permission)

    role = Role(
        name="admin",
        description="Administrator role",
        is_system=True,
        is_admin=True,
        permissions=[permission],
    )
    db_session.add(role)
    await db_session.flush()
    return role


@pytest.fixture
async def test_user(db_session: AsyncSession, test_role: Role) -> User:
    """Create a test user."""
    user = User(
        email="testuser@example.com",
        hashed_password=hash_password("password123"),
        first_name="Test",
        last_name="User",
        role_id=test_role.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def auth_headers(db_session: AsyncSession, test_user: User) -> dict[str, str]:
    """Create auth headers for test user."""
    auth_service = AuthService(db_session)
    tokens = await auth_service.create_tokens(test_user)
    return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest.fixture
async def test_project(db_session: AsyncSession, test_user: User):
    """Create a test project."""
    service = ProjectService(db_session)
    project = await service.create_project(
        key="TEST",
        name="Test Project",
        owner_id=test_user.id,
    )
    return project


@pytest.fixture
async def test_issue_type(db_session: AsyncSession) -> IssueType:
    """Create a test issue type."""
    issue_type = IssueType(
        project_id=None,
        name="Task",
        description="A task",
        icon="task",
        color="#3b82f6",
        is_subtask=True,
        position=0,
    )
    db_session.add(issue_type)
    await db_session.flush()
    return issue_type


@pytest.fixture
async def test_status(db_session: AsyncSession) -> Status:
    """Create a test status."""
    status = Status(
        project_id=None,
        name="To Do",
        description="Work not started",
        category=StatusCategory.TODO,
        color="#6b7280",
        position=0,
    )
    db_session.add(status)
    await db_session.flush()
    return status


@pytest.fixture
async def test_issue(
    db_session: AsyncSession,
    test_project,
    test_user: User,
    test_issue_type: IssueType,
    test_status: Status,
):
    """Create a test issue."""
    service = IssueService(db_session)
    issue = await service.create_issue(
        project_id=test_project.id,
        title="Test Issue",
        type_id=test_issue_type.id,
        reporter_id=test_user.id,
        status_id=test_status.id,
        priority=Priority.MEDIUM,
    )
    return issue


# =============================================================================
# Issue Type and Status Routes Tests
# =============================================================================


@pytest.mark.asyncio
async def test_list_issue_types(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_project,
    test_issue_type: IssueType,
) -> None:
    """GET /api/v1/projects/{key}/issue-types should return issue types."""
    response = await client.get(
        f"/api/v1/projects/{test_project.key}/issue-types",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_list_statuses(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_project,
    test_status: Status,
) -> None:
    """GET /api/v1/projects/{key}/statuses should return statuses."""
    response = await client.get(
        f"/api/v1/projects/{test_project.key}/statuses",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


# =============================================================================
# Issue CRUD Routes Tests
# =============================================================================


@pytest.mark.asyncio
async def test_create_issue(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_project,
    test_issue_type: IssueType,
    test_status: Status,
) -> None:
    """POST /api/v1/projects/{key}/issues should create issue."""
    response = await client.post(
        f"/api/v1/projects/{test_project.key}/issues",
        headers=auth_headers,
        json={
            "title": "New Issue",
            "type_id": str(test_issue_type.id),
            "status_id": str(test_status.id),
            "priority": "high",
            "description": "Issue description",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Issue"
    assert data["key"] == "TEST-1"
    assert data["priority"] == "high"


@pytest.mark.asyncio
async def test_list_issues(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_project,
    test_issue,
) -> None:
    """GET /api/v1/projects/{key}/issues should return issues."""
    response = await client.get(
        f"/api/v1/projects/{test_project.key}/issues",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_issue(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_issue,
) -> None:
    """GET /api/v1/issues/{key} should return issue details."""
    response = await client.get(
        f"/api/v1/issues/{test_issue.key}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["key"] == test_issue.key
    assert data["title"] == "Test Issue"


@pytest.mark.asyncio
async def test_get_issue_not_found(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """GET /api/v1/issues/{key} should return 404 for non-existent issue."""
    response = await client.get(
        "/api/v1/issues/NOTFOUND-999",
        headers=auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_issue(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_issue,
) -> None:
    """PATCH /api/v1/issues/{key} should update issue."""
    response = await client.patch(
        f"/api/v1/issues/{test_issue.key}",
        headers=auth_headers,
        json={
            "title": "Updated Title",
            "priority": "critical",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["priority"] == "critical"


@pytest.mark.asyncio
async def test_delete_issue(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_issue,
) -> None:
    """DELETE /api/v1/issues/{key} should soft delete issue."""
    response = await client.delete(
        f"/api/v1/issues/{test_issue.key}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    # Verify it's deleted (should return 404 now)
    get_response = await client.get(
        f"/api/v1/issues/{test_issue.key}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404


# =============================================================================
# Label Routes Tests
# =============================================================================


@pytest.mark.asyncio
async def test_create_label(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_project,
) -> None:
    """POST /api/v1/projects/{key}/labels should create label."""
    response = await client.post(
        f"/api/v1/projects/{test_project.key}/labels",
        headers=auth_headers,
        json={
            "name": "Bug",
            "color": "#ef4444",
            "description": "Bug label",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Bug"
    assert data["color"] == "#ef4444"


@pytest.mark.asyncio
async def test_list_labels(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_project,
    db_session: AsyncSession,
) -> None:
    """GET /api/v1/projects/{key}/labels should return labels."""
    # Create a label first
    from groundwork.issues.services import LabelService

    label_service = LabelService(db_session)
    await label_service.create_label(test_project.id, "Feature", "#8b5cf6")

    response = await client.get(
        f"/api/v1/projects/{test_project.key}/labels",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_update_label(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_project,
    db_session: AsyncSession,
) -> None:
    """PATCH /api/v1/labels/{id} should update label."""
    from groundwork.issues.services import LabelService

    label_service = LabelService(db_session)
    label = await label_service.create_label(test_project.id, "Bug", "#ef4444")

    response = await client.patch(
        f"/api/v1/labels/{label.id}",
        headers=auth_headers,
        json={"name": "Critical Bug", "color": "#dc2626"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Critical Bug"


@pytest.mark.asyncio
async def test_delete_label(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_project,
    db_session: AsyncSession,
) -> None:
    """DELETE /api/v1/labels/{id} should delete label."""
    from groundwork.issues.services import LabelService

    label_service = LabelService(db_session)
    label = await label_service.create_label(test_project.id, "Temp", "#999999")

    response = await client.delete(
        f"/api/v1/labels/{label.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204


# =============================================================================
# Subtask Routes Tests
# =============================================================================


@pytest.mark.asyncio
async def test_list_subtasks(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_issue,
    test_user: User,
    test_issue_type: IssueType,
    test_status: Status,
    db_session: AsyncSession,
) -> None:
    """GET /api/v1/issues/{key}/subtasks should return subtasks."""
    # Create a subtask
    issue_service = IssueService(db_session)
    await issue_service.create_issue(
        project_id=test_issue.project_id,
        title="Subtask",
        type_id=test_issue_type.id,
        reporter_id=test_user.id,
        status_id=test_status.id,
        parent_id=test_issue.id,
    )

    response = await client.get(
        f"/api/v1/issues/{test_issue.key}/subtasks",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_create_subtask(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_issue,
    test_issue_type: IssueType,
) -> None:
    """POST /api/v1/issues/{key}/subtasks should create subtask."""
    response = await client.post(
        f"/api/v1/issues/{test_issue.key}/subtasks",
        headers=auth_headers,
        json={
            "title": "New Subtask",
            "type_id": str(test_issue_type.id),
            "priority": "low",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Subtask"
    assert data["parent_id"] == str(test_issue.id)


# =============================================================================
# Issue Label Routes Tests
# =============================================================================


@pytest.mark.asyncio
async def test_add_label_to_issue(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_issue,
    test_project,
    db_session: AsyncSession,
) -> None:
    """POST /api/v1/issues/{key}/labels should add label to issue."""
    from groundwork.issues.services import LabelService

    label_service = LabelService(db_session)
    label = await label_service.create_label(test_project.id, "Bug", "#ef4444")

    response = await client.post(
        f"/api/v1/issues/{test_issue.key}/labels",
        headers=auth_headers,
        json={"label_id": str(label.id)},
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data["labels"]) == 1


@pytest.mark.asyncio
async def test_remove_label_from_issue(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_issue,
    test_project,
    db_session: AsyncSession,
) -> None:
    """DELETE /api/v1/issues/{key}/labels/{id} should remove label."""
    from groundwork.issues.services import IssueService, LabelService

    label_service = LabelService(db_session)
    issue_service = IssueService(db_session)

    label = await label_service.create_label(test_project.id, "Bug", "#ef4444")
    await issue_service.add_label(test_issue.id, label.id)

    response = await client.delete(
        f"/api/v1/issues/{test_issue.key}/labels/{label.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204
