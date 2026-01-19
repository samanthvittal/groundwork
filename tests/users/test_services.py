"""Tests for user management services."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.models import Permission, Role, User
from groundwork.auth.utils import hash_password, verify_password


@pytest.fixture
async def test_role(db_session: AsyncSession) -> Role:
    """Create a test role."""
    # Create a permission first
    permission = Permission(
        codename="users:read",
        description="Can read users",
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
        email="existing@example.com",
        hashed_password=hash_password("password123"),
        first_name="Existing",
        last_name="User",
        role_id=test_role.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.mark.asyncio
async def test_user_service_list_users(
    db_session: AsyncSession, test_user: User
) -> None:
    """UserService.list_users should return paginated users."""
    from groundwork.users.services import UserService

    service = UserService(db_session)
    users = await service.list_users(skip=0, limit=100)

    assert len(users) >= 1
    assert any(u.email == "existing@example.com" for u in users)


@pytest.mark.asyncio
async def test_user_service_list_users_pagination(
    db_session: AsyncSession, test_role: Role
) -> None:
    """UserService.list_users should respect pagination params."""
    from groundwork.users.services import UserService

    # Create multiple users
    for i in range(5):
        user = User(
            email=f"user{i}@example.com",
            hashed_password=hash_password("password123"),
            first_name=f"User{i}",
            last_name="Test",
            role_id=test_role.id,
        )
        db_session.add(user)
    await db_session.flush()

    service = UserService(db_session)

    # Get first 2 users
    users = await service.list_users(skip=0, limit=2)
    assert len(users) == 2

    # Get next 2 users
    users_next = await service.list_users(skip=2, limit=2)
    assert len(users_next) == 2

    # Ensure different users
    first_emails = {u.email for u in users}
    next_emails = {u.email for u in users_next}
    assert first_emails.isdisjoint(next_emails)


@pytest.mark.asyncio
async def test_user_service_get_user(db_session: AsyncSession, test_user: User) -> None:
    """UserService.get_user should return user by ID."""
    from groundwork.users.services import UserService

    service = UserService(db_session)
    user = await service.get_user(test_user.id)

    assert user is not None
    assert user.email == "existing@example.com"


@pytest.mark.asyncio
async def test_user_service_get_user_not_found(db_session: AsyncSession) -> None:
    """UserService.get_user should return None for unknown ID."""
    from groundwork.users.services import UserService

    service = UserService(db_session)
    user = await service.get_user(uuid4())

    assert user is None


@pytest.mark.asyncio
async def test_user_service_create_user(
    db_session: AsyncSession, test_role: Role
) -> None:
    """UserService.create_user should create a new user."""
    from groundwork.users.services import UserService

    service = UserService(db_session)
    user = await service.create_user(
        email="new@example.com",
        password="password123",
        first_name="New",
        last_name="User",
        role_id=test_role.id,
    )

    assert user is not None
    assert user.email == "new@example.com"
    assert user.first_name == "New"
    assert user.last_name == "User"
    assert user.is_active is True
    assert verify_password("password123", user.hashed_password)


@pytest.mark.asyncio
async def test_user_service_create_user_duplicate_email(
    db_session: AsyncSession, test_user: User, test_role: Role
) -> None:
    """UserService.create_user should return None for duplicate email."""
    from groundwork.users.services import UserService

    service = UserService(db_session)
    user = await service.create_user(
        email="existing@example.com",  # Already exists
        password="password123",
        first_name="Duplicate",
        last_name="User",
        role_id=test_role.id,
    )

    assert user is None


@pytest.mark.asyncio
async def test_user_service_create_user_with_optional_fields(
    db_session: AsyncSession, test_role: Role
) -> None:
    """UserService.create_user should accept optional fields."""
    from groundwork.users.services import UserService

    service = UserService(db_session)
    user = await service.create_user(
        email="optional@example.com",
        password="password123",
        first_name="Optional",
        last_name="User",
        role_id=test_role.id,
        display_name="Optie",
        timezone="America/New_York",
        language="es",
        theme="dark",
    )

    assert user is not None
    assert user.display_name == "Optie"
    assert user.timezone == "America/New_York"
    assert user.language == "es"
    assert user.theme == "dark"


@pytest.mark.asyncio
async def test_user_service_update_user(
    db_session: AsyncSession, test_user: User
) -> None:
    """UserService.update_user should update user fields."""
    from groundwork.users.services import UserService

    service = UserService(db_session)
    user = await service.update_user(
        user_id=test_user.id,
        first_name="Updated",
        display_name="Updated Display",
    )

    assert user is not None
    assert user.first_name == "Updated"
    assert user.display_name == "Updated Display"
    # Unchanged fields should remain
    assert user.last_name == "User"


@pytest.mark.asyncio
async def test_user_service_update_user_not_found(db_session: AsyncSession) -> None:
    """UserService.update_user should return None for unknown ID."""
    from groundwork.users.services import UserService

    service = UserService(db_session)
    user = await service.update_user(
        user_id=uuid4(),
        first_name="Updated",
    )

    assert user is None


@pytest.mark.asyncio
async def test_user_service_deactivate_user(
    db_session: AsyncSession, test_user: User
) -> None:
    """UserService.deactivate_user should set is_active=False."""
    from groundwork.users.services import UserService

    service = UserService(db_session)
    result = await service.deactivate_user(test_user.id)

    assert result is True

    # Verify user is deactivated
    user = await service.get_user(test_user.id)
    assert user is not None
    assert user.is_active is False


@pytest.mark.asyncio
async def test_user_service_deactivate_user_not_found(db_session: AsyncSession) -> None:
    """UserService.deactivate_user should return False for unknown ID."""
    from groundwork.users.services import UserService

    service = UserService(db_session)
    result = await service.deactivate_user(uuid4())

    assert result is False


@pytest.mark.asyncio
async def test_user_service_reset_password(
    db_session: AsyncSession, test_user: User
) -> None:
    """UserService.reset_password should update password without old password."""
    from groundwork.users.services import UserService

    service = UserService(db_session)
    result = await service.reset_password(test_user.id, "newpassword123")

    assert result is True

    # Verify password changed
    user = await service.get_user(test_user.id)
    assert user is not None
    assert verify_password("newpassword123", user.hashed_password)


@pytest.mark.asyncio
async def test_user_service_reset_password_not_found(db_session: AsyncSession) -> None:
    """UserService.reset_password should return False for unknown ID."""
    from groundwork.users.services import UserService

    service = UserService(db_session)
    result = await service.reset_password(uuid4(), "newpassword123")

    assert result is False
