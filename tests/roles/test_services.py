"""Tests for role management services."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.models import Permission, Role


@pytest.fixture
async def test_permission(db_session: AsyncSession) -> Permission:
    """Create a test permission."""
    permission = Permission(
        id=uuid4(),
        codename="test:permission",
        description="Test permission",
    )
    db_session.add(permission)
    await db_session.flush()
    return permission


@pytest.fixture
async def test_permission_2(db_session: AsyncSession) -> Permission:
    """Create a second test permission."""
    permission = Permission(
        id=uuid4(),
        codename="test:permission2",
        description="Test permission 2",
    )
    db_session.add(permission)
    await db_session.flush()
    return permission


@pytest.fixture
async def test_role(db_session: AsyncSession, test_permission: Permission) -> Role:
    """Create a test role."""
    role = Role(
        id=uuid4(),
        name="test_role",
        description="A test role",
        is_system=False,
    )
    role.permissions.append(test_permission)
    db_session.add(role)
    await db_session.flush()
    return role


@pytest.fixture
async def system_role(db_session: AsyncSession) -> Role:
    """Create a system role."""
    role = Role(
        id=uuid4(),
        name="system_role",
        description="A system role",
        is_system=True,
    )
    db_session.add(role)
    await db_session.flush()
    return role


# =============================================================================
# list_roles
# =============================================================================


@pytest.mark.asyncio
async def test_list_roles_returns_all_roles(
    db_session: AsyncSession, test_role: Role, system_role: Role
) -> None:
    """list_roles should return all roles."""
    from groundwork.roles.services import RoleService

    service = RoleService(db_session)
    roles = await service.list_roles()

    assert len(roles) == 2
    role_names = [r.name for r in roles]
    assert "test_role" in role_names
    assert "system_role" in role_names


@pytest.mark.asyncio
async def test_list_roles_empty_database(db_session: AsyncSession) -> None:
    """list_roles should return empty list when no roles exist."""
    from groundwork.roles.services import RoleService

    service = RoleService(db_session)
    roles = await service.list_roles()

    assert roles == []


# =============================================================================
# get_role
# =============================================================================


@pytest.mark.asyncio
async def test_get_role_returns_role_with_permissions(
    db_session: AsyncSession, test_role: Role, test_permission: Permission
) -> None:
    """get_role should return role with permissions loaded."""
    from groundwork.roles.services import RoleService

    service = RoleService(db_session)
    role = await service.get_role(test_role.id)

    assert role is not None
    assert role.name == "test_role"
    assert len(role.permissions) == 1
    assert role.permissions[0].codename == "test:permission"


@pytest.mark.asyncio
async def test_get_role_not_found(db_session: AsyncSession) -> None:
    """get_role should return None for non-existent role."""
    from groundwork.roles.services import RoleService

    service = RoleService(db_session)
    role = await service.get_role(uuid4())

    assert role is None


# =============================================================================
# create_role
# =============================================================================


@pytest.mark.asyncio
async def test_create_role_success(
    db_session: AsyncSession, test_permission: Permission
) -> None:
    """create_role should create a new role with permissions."""
    from groundwork.roles.services import RoleService

    service = RoleService(db_session)
    role = await service.create_role(
        name="new_role",
        description="A new role",
        permission_ids=[test_permission.id],
    )

    assert role is not None
    assert role.name == "new_role"
    assert role.description == "A new role"
    assert role.is_system is False
    assert len(role.permissions) == 1


@pytest.mark.asyncio
async def test_create_role_without_permissions(db_session: AsyncSession) -> None:
    """create_role should create a role with no permissions."""
    from groundwork.roles.services import RoleService

    service = RoleService(db_session)
    role = await service.create_role(
        name="empty_role",
        description="A role with no permissions",
        permission_ids=[],
    )

    assert role is not None
    assert role.name == "empty_role"
    assert len(role.permissions) == 0


@pytest.mark.asyncio
async def test_create_role_duplicate_name_returns_none(
    db_session: AsyncSession, test_role: Role
) -> None:
    """create_role should return None for duplicate name."""
    from groundwork.roles.services import RoleService

    service = RoleService(db_session)
    role = await service.create_role(
        name="test_role",  # Same as existing test_role
        description="Duplicate",
        permission_ids=[],
    )

    assert role is None


# =============================================================================
# update_role
# =============================================================================


@pytest.mark.asyncio
async def test_update_role_name(db_session: AsyncSession, test_role: Role) -> None:
    """update_role should update role name."""
    from groundwork.roles.services import RoleService

    service = RoleService(db_session)
    role = await service.update_role(
        role_id=test_role.id,
        name="updated_name",
    )

    assert role is not None
    assert role.name == "updated_name"


@pytest.mark.asyncio
async def test_update_role_description(
    db_session: AsyncSession, test_role: Role
) -> None:
    """update_role should update role description."""
    from groundwork.roles.services import RoleService

    service = RoleService(db_session)
    role = await service.update_role(
        role_id=test_role.id,
        description="Updated description",
    )

    assert role is not None
    assert role.description == "Updated description"


@pytest.mark.asyncio
async def test_update_role_permissions(
    db_session: AsyncSession, test_role: Role, test_permission_2: Permission
) -> None:
    """update_role should update role permissions."""
    from groundwork.roles.services import RoleService

    service = RoleService(db_session)
    role = await service.update_role(
        role_id=test_role.id,
        permission_ids=[test_permission_2.id],
    )

    assert role is not None
    assert len(role.permissions) == 1
    assert role.permissions[0].codename == "test:permission2"


@pytest.mark.asyncio
async def test_update_role_not_found(db_session: AsyncSession) -> None:
    """update_role should return None for non-existent role."""
    from groundwork.roles.services import RoleService

    service = RoleService(db_session)
    role = await service.update_role(
        role_id=uuid4(),
        name="nonexistent",
    )

    assert role is None


@pytest.mark.asyncio
async def test_update_role_duplicate_name(db_session: AsyncSession) -> None:
    """update_role should return 'duplicate' when renaming to existing name."""
    from groundwork.roles.services import RoleService

    service = RoleService(db_session)

    # Create two roles
    role1 = await service.create_role(
        name="role_one",
        description="First role",
        permission_ids=[],
    )
    await service.create_role(
        name="role_two",
        description="Second role",
        permission_ids=[],
    )

    assert role1 is not None

    # Try to rename role1 to role_two's name
    result = await service.update_role(
        role_id=role1.id,
        name="role_two",
    )

    assert result == "duplicate"


@pytest.mark.asyncio
async def test_update_role_same_name_allowed(db_session: AsyncSession) -> None:
    """update_role should allow updating a role to its own name."""
    from groundwork.roles.services import RoleService

    service = RoleService(db_session)

    # Create a role
    role = await service.create_role(
        name="same_name_role",
        description="Test role",
        permission_ids=[],
    )

    assert role is not None

    # Update with same name should succeed
    result = await service.update_role(
        role_id=role.id,
        name="same_name_role",
        description="Updated description",
    )

    assert result is not None
    assert result != "duplicate"
    assert result.description == "Updated description"


# =============================================================================
# delete_role
# =============================================================================


@pytest.mark.asyncio
async def test_delete_role_success(db_session: AsyncSession, test_role: Role) -> None:
    """delete_role should delete custom role and return True."""
    from groundwork.roles.services import RoleService

    service = RoleService(db_session)
    result = await service.delete_role(test_role.id)

    assert result is True

    # Verify role is deleted
    deleted_role = await service.get_role(test_role.id)
    assert deleted_role is None


@pytest.mark.asyncio
async def test_delete_role_refuses_system_role(
    db_session: AsyncSession, system_role: Role
) -> None:
    """delete_role should return 'system' for system roles."""
    from groundwork.roles.services import RoleService

    service = RoleService(db_session)
    result = await service.delete_role(system_role.id)

    assert result == "system"

    # Verify role still exists
    role = await service.get_role(system_role.id)
    assert role is not None


@pytest.mark.asyncio
async def test_delete_role_not_found(db_session: AsyncSession) -> None:
    """delete_role should return False for non-existent role."""
    from groundwork.roles.services import RoleService

    service = RoleService(db_session)
    result = await service.delete_role(uuid4())

    assert result is False


# =============================================================================
# list_permissions
# =============================================================================


@pytest.mark.asyncio
async def test_list_permissions_returns_all_permissions(
    db_session: AsyncSession, test_permission: Permission, test_permission_2: Permission
) -> None:
    """list_permissions should return all permissions."""
    from groundwork.roles.services import RoleService

    service = RoleService(db_session)
    permissions = await service.list_permissions()

    assert len(permissions) == 2
    codenames = [p.codename for p in permissions]
    assert "test:permission" in codenames
    assert "test:permission2" in codenames


@pytest.mark.asyncio
async def test_list_permissions_empty_database(db_session: AsyncSession) -> None:
    """list_permissions should return empty list when no permissions exist."""
    from groundwork.roles.services import RoleService

    service = RoleService(db_session)
    permissions = await service.list_permissions()

    assert permissions == []
