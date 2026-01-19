"""Tests for project models."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.models import Permission, Role, User
from groundwork.auth.utils import hash_password
from groundwork.projects.models import (
    Project,
    ProjectMember,
    ProjectRole,
    ProjectStatus,
    ProjectVisibility,
)


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


@pytest.mark.asyncio
async def test_project_model_creates(db_session: AsyncSession, test_user: User) -> None:
    """Project should be created with required fields."""
    project = Project(
        key="TEST",
        name="Test Project",
        owner_id=test_user.id,
    )
    db_session.add(project)
    await db_session.flush()

    assert project.id is not None
    assert project.key == "TEST"
    assert project.name == "Test Project"
    assert project.owner_id == test_user.id
    assert project.status == ProjectStatus.ACTIVE
    assert project.visibility == ProjectVisibility.PRIVATE


@pytest.mark.asyncio
async def test_project_with_description(
    db_session: AsyncSession, test_user: User
) -> None:
    """Project should store description."""
    project = Project(
        key="PROJ",
        name="Project with Description",
        description="This is a test project",
        owner_id=test_user.id,
    )
    db_session.add(project)
    await db_session.flush()

    assert project.description == "This is a test project"


@pytest.mark.asyncio
async def test_project_status_enum(db_session: AsyncSession, test_user: User) -> None:
    """Project status should be settable."""
    project = Project(
        key="ARCH",
        name="Archived Project",
        owner_id=test_user.id,
        status=ProjectStatus.ARCHIVED,
    )
    db_session.add(project)
    await db_session.flush()

    assert project.status == ProjectStatus.ARCHIVED


@pytest.mark.asyncio
async def test_project_visibility_enum(
    db_session: AsyncSession, test_user: User
) -> None:
    """Project visibility should be settable."""
    project = Project(
        key="INT",
        name="Internal Project",
        owner_id=test_user.id,
        visibility=ProjectVisibility.INTERNAL,
    )
    db_session.add(project)
    await db_session.flush()

    assert project.visibility == ProjectVisibility.INTERNAL


@pytest.mark.asyncio
async def test_project_member_count(db_session: AsyncSession, test_user: User) -> None:
    """Project should track member count."""
    project = Project(
        key="MEMB",
        name="Project with Members",
        owner_id=test_user.id,
    )
    db_session.add(project)
    await db_session.flush()

    # Add member
    member = ProjectMember(
        project_id=project.id,
        user_id=test_user.id,
        role=ProjectRole.OWNER,
    )
    db_session.add(member)
    await db_session.flush()

    # Refresh to get updated relationships
    await db_session.refresh(project, ["members"])

    assert project.member_count == 1


@pytest.mark.asyncio
async def test_project_member_creates(
    db_session: AsyncSession, test_user: User
) -> None:
    """ProjectMember should be created with required fields."""
    project = Project(
        key="PM",
        name="Project for Member",
        owner_id=test_user.id,
    )
    db_session.add(project)
    await db_session.flush()

    member = ProjectMember(
        project_id=project.id,
        user_id=test_user.id,
        role=ProjectRole.OWNER,
    )
    db_session.add(member)
    await db_session.flush()

    assert member.id is not None
    assert member.project_id == project.id
    assert member.user_id == test_user.id
    assert member.role == ProjectRole.OWNER
    assert member.joined_at is not None


@pytest.mark.asyncio
async def test_project_member_role_default(
    db_session: AsyncSession, test_user: User
) -> None:
    """ProjectMember role should default to MEMBER."""
    project = Project(
        key="DEF",
        name="Default Role Project",
        owner_id=test_user.id,
    )
    db_session.add(project)
    await db_session.flush()

    member = ProjectMember(
        project_id=project.id,
        user_id=test_user.id,
    )
    db_session.add(member)
    await db_session.flush()

    assert member.role == ProjectRole.MEMBER


@pytest.mark.asyncio
async def test_project_owner_relationship(
    db_session: AsyncSession, test_user: User
) -> None:
    """Project should have owner relationship."""
    project = Project(
        key="OWN",
        name="Owner Relationship Project",
        owner_id=test_user.id,
    )
    db_session.add(project)
    await db_session.flush()

    # Refresh to get relationship
    await db_session.refresh(project, ["owner"])

    assert project.owner is not None
    assert project.owner.id == test_user.id
    assert project.owner.email == "testuser@example.com"
