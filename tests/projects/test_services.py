"""Tests for project services."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.models import Permission, Role, User
from groundwork.auth.utils import hash_password
from groundwork.projects.models import (
    Project,
    ProjectRole,
    ProjectStatus,
    ProjectVisibility,
)
from groundwork.projects.services import ProjectService


@pytest.fixture
async def test_role(db_session: AsyncSession) -> Role:
    """Create a test role."""
    permission = Permission(
        codename="projects:read",
        description="Can read projects",
    )
    db_session.add(permission)

    role = Role(
        name="admin",
        description="Administrator role",
        is_system=True,
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
async def second_user(db_session: AsyncSession, test_role: Role) -> User:
    """Create a second test user."""
    user = User(
        email="second@example.com",
        hashed_password=hash_password("password123"),
        first_name="Second",
        last_name="User",
        role_id=test_role.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def test_project(db_session: AsyncSession, test_user: User) -> Project:
    """Create a test project with owner as member."""
    service = ProjectService(db_session)
    project = await service.create_project(
        key="TEST",
        name="Test Project",
        owner_id=test_user.id,
        description="A test project",
    )
    return project


# Project CRUD Tests


@pytest.mark.asyncio
async def test_create_project_success(
    db_session: AsyncSession, test_user: User
) -> None:
    """ProjectService.create_project should create project and add owner as member."""
    service = ProjectService(db_session)
    project = await service.create_project(
        key="NEW",
        name="New Project",
        owner_id=test_user.id,
        description="A new project",
        visibility=ProjectVisibility.INTERNAL,
    )

    assert project is not None
    assert project.key == "NEW"
    assert project.name == "New Project"
    assert project.description == "A new project"
    assert project.visibility == ProjectVisibility.INTERNAL
    assert project.owner_id == test_user.id
    # Owner should be added as member
    assert len(project.members) == 1
    assert project.members[0].user_id == test_user.id
    assert project.members[0].role == ProjectRole.OWNER


@pytest.mark.asyncio
async def test_create_project_duplicate_key(
    db_session: AsyncSession, test_user: User, test_project: Project
) -> None:
    """ProjectService.create_project should return None for duplicate key."""
    service = ProjectService(db_session)
    project = await service.create_project(
        key="TEST",  # Same key as test_project
        name="Another Project",
        owner_id=test_user.id,
    )

    assert project is None


@pytest.mark.asyncio
async def test_create_project_uppercase_key(
    db_session: AsyncSession, test_user: User
) -> None:
    """ProjectService.create_project should uppercase the key."""
    service = ProjectService(db_session)
    project = await service.create_project(
        key="lower",
        name="Lowercase Key Project",
        owner_id=test_user.id,
    )

    assert project is not None
    assert project.key == "LOWER"


@pytest.mark.asyncio
async def test_get_project_by_id(
    db_session: AsyncSession, test_project: Project
) -> None:
    """ProjectService.get_project should return project by ID."""
    service = ProjectService(db_session)
    project = await service.get_project(test_project.id)

    assert project is not None
    assert project.id == test_project.id
    assert project.key == "TEST"


@pytest.mark.asyncio
async def test_get_project_not_found(db_session: AsyncSession) -> None:
    """ProjectService.get_project should return None for non-existent ID."""
    from uuid import uuid4

    service = ProjectService(db_session)
    project = await service.get_project(uuid4())

    assert project is None


@pytest.mark.asyncio
async def test_get_project_by_key(
    db_session: AsyncSession, test_project: Project
) -> None:
    """ProjectService.get_project_by_key should return project by key."""
    service = ProjectService(db_session)
    project = await service.get_project_by_key("TEST")

    assert project is not None
    assert project.key == "TEST"


@pytest.mark.asyncio
async def test_list_projects(db_session: AsyncSession, test_project: Project) -> None:
    """ProjectService.list_projects should return all projects."""
    service = ProjectService(db_session)
    projects = await service.list_projects()

    assert len(projects) >= 1
    assert any(p.key == "TEST" for p in projects)


@pytest.mark.asyncio
async def test_list_projects_filter_by_status(
    db_session: AsyncSession, test_user: User
) -> None:
    """ProjectService.list_projects should filter by status."""
    service = ProjectService(db_session)

    # Create an archived project
    archived = await service.create_project(
        key="ARCH",
        name="Archived Project",
        owner_id=test_user.id,
    )
    await service.archive_project(archived.id)

    # Create an active project
    await service.create_project(
        key="ACT",
        name="Active Project",
        owner_id=test_user.id,
    )

    # List only active
    active_projects = await service.list_projects(status=ProjectStatus.ACTIVE)
    assert all(p.status == ProjectStatus.ACTIVE for p in active_projects)

    # List only archived
    archived_projects = await service.list_projects(status=ProjectStatus.ARCHIVED)
    assert all(p.status == ProjectStatus.ARCHIVED for p in archived_projects)


@pytest.mark.asyncio
async def test_list_user_projects(
    db_session: AsyncSession, test_user: User, second_user: User
) -> None:
    """ProjectService.list_user_projects should return user's projects."""
    service = ProjectService(db_session)

    # Create projects for test_user
    await service.create_project(
        key="USR1",
        name="User Project 1",
        owner_id=test_user.id,
    )

    # Create project for second_user
    await service.create_project(
        key="OTH",
        name="Other User Project",
        owner_id=second_user.id,
    )

    # List test_user's projects
    user_projects = await service.list_user_projects(test_user.id)

    assert len(user_projects) >= 1
    assert all(
        p.owner_id == test_user.id or any(m.user_id == test_user.id for m in p.members)
        for p in user_projects
    )


@pytest.mark.asyncio
async def test_update_project(db_session: AsyncSession, test_project: Project) -> None:
    """ProjectService.update_project should update project fields."""
    service = ProjectService(db_session)
    project = await service.update_project(
        project_id=test_project.id,
        name="Updated Name",
        description="Updated description",
        visibility=ProjectVisibility.INTERNAL,
    )

    assert project is not None
    assert project.name == "Updated Name"
    assert project.description == "Updated description"
    assert project.visibility == ProjectVisibility.INTERNAL


@pytest.mark.asyncio
async def test_update_project_not_found(db_session: AsyncSession) -> None:
    """ProjectService.update_project should return None for non-existent project."""
    from uuid import uuid4

    service = ProjectService(db_session)
    project = await service.update_project(
        project_id=uuid4(),
        name="Updated Name",
    )

    assert project is None


@pytest.mark.asyncio
async def test_archive_project(db_session: AsyncSession, test_project: Project) -> None:
    """ProjectService.archive_project should set status to archived."""
    service = ProjectService(db_session)
    project = await service.archive_project(test_project.id)

    assert project is not None
    assert project.status == ProjectStatus.ARCHIVED
    assert project.archived_at is not None


@pytest.mark.asyncio
async def test_restore_project(db_session: AsyncSession, test_project: Project) -> None:
    """ProjectService.restore_project should restore archived project to active."""
    service = ProjectService(db_session)

    # First archive the project
    await service.archive_project(test_project.id)

    # Then restore it
    project = await service.restore_project(test_project.id)

    assert project is not None
    assert project.status == ProjectStatus.ACTIVE
    assert project.archived_at is None


@pytest.mark.asyncio
async def test_delete_project(db_session: AsyncSession, test_project: Project) -> None:
    """ProjectService.delete_project should soft delete project."""
    service = ProjectService(db_session)
    result = await service.delete_project(test_project.id)

    assert result is True

    # Verify project is marked as deleted
    project = await service.get_project(test_project.id)
    assert project.status == ProjectStatus.DELETED


# Member Management Tests


@pytest.mark.asyncio
async def test_add_member(
    db_session: AsyncSession, test_project: Project, second_user: User
) -> None:
    """ProjectService.add_member should add user to project."""
    service = ProjectService(db_session)
    member = await service.add_member(
        project_id=test_project.id,
        user_id=second_user.id,
        role=ProjectRole.MEMBER,
    )

    assert member is not None
    assert member.user_id == second_user.id
    assert member.role == ProjectRole.MEMBER


@pytest.mark.asyncio
async def test_add_member_duplicate(
    db_session: AsyncSession, test_project: Project, test_user: User
) -> None:
    """ProjectService.add_member should return None for existing member."""
    service = ProjectService(db_session)
    # test_user is already owner/member from project creation
    member = await service.add_member(
        project_id=test_project.id,
        user_id=test_user.id,
        role=ProjectRole.MEMBER,
    )

    assert member is None


@pytest.mark.asyncio
async def test_update_member_role(
    db_session: AsyncSession, test_project: Project, second_user: User
) -> None:
    """ProjectService.update_member_role should update member's role."""
    service = ProjectService(db_session)

    # Add member first
    await service.add_member(
        project_id=test_project.id,
        user_id=second_user.id,
        role=ProjectRole.MEMBER,
    )

    # Update role
    member = await service.update_member_role(
        project_id=test_project.id,
        user_id=second_user.id,
        role=ProjectRole.ADMIN,
    )

    assert member is not None
    assert member.role == ProjectRole.ADMIN


@pytest.mark.asyncio
async def test_remove_member(
    db_session: AsyncSession, test_project: Project, second_user: User
) -> None:
    """ProjectService.remove_member should remove member from project."""
    service = ProjectService(db_session)

    # Add member first
    await service.add_member(
        project_id=test_project.id,
        user_id=second_user.id,
        role=ProjectRole.MEMBER,
    )

    # Remove member
    result = await service.remove_member(
        project_id=test_project.id,
        user_id=second_user.id,
    )

    assert result is True

    # Verify member is removed
    member = await service.get_member(test_project.id, second_user.id)
    assert member is None


@pytest.mark.asyncio
async def test_list_project_members(
    db_session: AsyncSession, test_project: Project, second_user: User
) -> None:
    """ProjectService.list_project_members should return all members."""
    service = ProjectService(db_session)

    # Add second member
    await service.add_member(
        project_id=test_project.id,
        user_id=second_user.id,
        role=ProjectRole.MEMBER,
    )

    members = await service.list_project_members(test_project.id)

    assert len(members) == 2


# Permission Check Tests


@pytest.mark.asyncio
async def test_user_can_access_owner(
    db_session: AsyncSession, test_project: Project, test_user: User
) -> None:
    """Owner should have access to project."""
    service = ProjectService(db_session)
    can_access = await service.user_can_access(test_project.id, test_user.id)

    assert can_access is True


@pytest.mark.asyncio
async def test_user_can_access_member(
    db_session: AsyncSession, test_project: Project, second_user: User
) -> None:
    """Member should have access to private project."""
    service = ProjectService(db_session)

    # Add as member
    await service.add_member(
        project_id=test_project.id,
        user_id=second_user.id,
        role=ProjectRole.VIEWER,
    )

    can_access = await service.user_can_access(test_project.id, second_user.id)

    assert can_access is True


@pytest.mark.asyncio
async def test_user_can_access_internal(
    db_session: AsyncSession, test_user: User, second_user: User
) -> None:
    """Any user should have access to internal project."""
    service = ProjectService(db_session)

    # Create internal project
    project = await service.create_project(
        key="INT",
        name="Internal Project",
        owner_id=test_user.id,
        visibility=ProjectVisibility.INTERNAL,
    )

    # Second user (not a member) should have access
    can_access = await service.user_can_access(project.id, second_user.id)

    assert can_access is True


@pytest.mark.asyncio
async def test_user_cannot_access_private(
    db_session: AsyncSession, test_project: Project, second_user: User
) -> None:
    """Non-member should not have access to private project."""
    service = ProjectService(db_session)

    can_access = await service.user_can_access(test_project.id, second_user.id)

    assert can_access is False


@pytest.mark.asyncio
async def test_user_can_edit_member(
    db_session: AsyncSession, test_project: Project, second_user: User
) -> None:
    """Member should be able to edit project."""
    service = ProjectService(db_session)

    # Add as member
    await service.add_member(
        project_id=test_project.id,
        user_id=second_user.id,
        role=ProjectRole.MEMBER,
    )

    can_edit = await service.user_can_edit(test_project.id, second_user.id)

    assert can_edit is True


@pytest.mark.asyncio
async def test_user_cannot_edit_viewer(
    db_session: AsyncSession, test_project: Project, second_user: User
) -> None:
    """Viewer should not be able to edit project."""
    service = ProjectService(db_session)

    # Add as viewer
    await service.add_member(
        project_id=test_project.id,
        user_id=second_user.id,
        role=ProjectRole.VIEWER,
    )

    can_edit = await service.user_can_edit(test_project.id, second_user.id)

    assert can_edit is False


@pytest.mark.asyncio
async def test_user_can_admin_owner(
    db_session: AsyncSession, test_project: Project, test_user: User
) -> None:
    """Owner should have admin access."""
    service = ProjectService(db_session)
    can_admin = await service.user_can_admin(test_project.id, test_user.id)

    assert can_admin is True


@pytest.mark.asyncio
async def test_user_can_admin_admin(
    db_session: AsyncSession, test_project: Project, second_user: User
) -> None:
    """Admin should have admin access."""
    service = ProjectService(db_session)

    # Add as admin
    await service.add_member(
        project_id=test_project.id,
        user_id=second_user.id,
        role=ProjectRole.ADMIN,
    )

    can_admin = await service.user_can_admin(test_project.id, second_user.id)

    assert can_admin is True


@pytest.mark.asyncio
async def test_user_cannot_admin_member(
    db_session: AsyncSession, test_project: Project, second_user: User
) -> None:
    """Member should not have admin access."""
    service = ProjectService(db_session)

    # Add as member
    await service.add_member(
        project_id=test_project.id,
        user_id=second_user.id,
        role=ProjectRole.MEMBER,
    )

    can_admin = await service.user_can_admin(test_project.id, second_user.id)

    assert can_admin is False


@pytest.mark.asyncio
async def test_user_is_owner(
    db_session: AsyncSession, test_project: Project, test_user: User
) -> None:
    """user_is_owner should return True for owner."""
    service = ProjectService(db_session)
    is_owner = await service.user_is_owner(test_project.id, test_user.id)

    assert is_owner is True


@pytest.mark.asyncio
async def test_user_is_not_owner(
    db_session: AsyncSession, test_project: Project, second_user: User
) -> None:
    """user_is_owner should return False for non-owner."""
    service = ProjectService(db_session)
    is_owner = await service.user_is_owner(test_project.id, second_user.id)

    assert is_owner is False
