"""Tests for default roles and permissions seeding."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from groundwork.auth.models import Permission, Role

# =============================================================================
# Default Permissions
# =============================================================================


@pytest.mark.asyncio
async def test_seed_defaults_creates_all_default_permissions(
    db_session: AsyncSession,
) -> None:
    """seed_defaults should create all default permissions."""
    from groundwork.core.seed import seed_defaults

    await seed_defaults(db_session)

    # Verify all expected permissions exist
    result = await db_session.execute(select(Permission))
    permissions = {p.codename: p.description for p in result.scalars().all()}

    expected_permissions = {
        "users:create": "Create new users",
        "users:read": "View user list and details",
        "users:update": "Edit user profiles and roles",
        "users:delete": "Deactivate/delete users",
        "roles:manage": "Create, edit, delete custom roles",
        "settings:manage": "Modify instance settings, SMTP config",
    }

    for codename, description in expected_permissions.items():
        assert codename in permissions, f"Permission {codename} should exist"
        assert permissions[codename] == description


@pytest.mark.asyncio
async def test_seed_defaults_is_idempotent_for_permissions(
    db_session: AsyncSession,
) -> None:
    """seed_defaults should not duplicate permissions when run multiple times."""
    from groundwork.core.seed import seed_defaults

    # Run twice
    await seed_defaults(db_session)
    await seed_defaults(db_session)

    # Count permissions
    result = await db_session.execute(select(Permission))
    permissions = list(result.scalars().all())

    # Should have exactly 6 permissions (no duplicates)
    assert len(permissions) == 6


@pytest.mark.asyncio
async def test_seed_defaults_preserves_existing_permissions(
    db_session: AsyncSession,
) -> None:
    """seed_defaults should not modify existing permissions."""
    from groundwork.core.seed import seed_defaults

    # Create a permission with different description
    existing_permission = Permission(
        codename="users:create",
        description="Custom description",
    )
    db_session.add(existing_permission)
    await db_session.flush()
    original_id = existing_permission.id

    await seed_defaults(db_session)

    # Verify original permission was not modified
    result = await db_session.execute(
        select(Permission).where(Permission.codename == "users:create")
    )
    permission = result.scalar_one()

    assert permission.id == original_id
    # Description should be preserved (not overwritten)
    assert permission.description == "Custom description"


# =============================================================================
# Default Roles
# =============================================================================


@pytest.mark.asyncio
async def test_seed_defaults_creates_admin_role_with_all_permissions(
    db_session: AsyncSession,
) -> None:
    """seed_defaults should create Admin role with all permissions."""
    from groundwork.core.seed import seed_defaults

    await seed_defaults(db_session)

    result = await db_session.execute(
        select(Role).where(Role.name == "Admin").options(selectinload(Role.permissions))
    )
    admin_role = result.scalar_one()

    assert admin_role.is_system is True
    assert admin_role.description == "Administrator with full access"

    permission_codenames = {p.codename for p in admin_role.permissions}
    expected = {
        "users:create",
        "users:read",
        "users:update",
        "users:delete",
        "roles:manage",
        "settings:manage",
    }
    assert permission_codenames == expected


@pytest.mark.asyncio
async def test_seed_defaults_creates_manager_role_with_user_permissions(
    db_session: AsyncSession,
) -> None:
    """seed_defaults should create Manager role with users:read, create, update."""
    from groundwork.core.seed import seed_defaults

    await seed_defaults(db_session)

    result = await db_session.execute(
        select(Role)
        .where(Role.name == "Manager")
        .options(selectinload(Role.permissions))
    )
    manager_role = result.scalar_one()

    assert manager_role.is_system is True
    assert manager_role.description == "Manager with user management access"

    permission_codenames = {p.codename for p in manager_role.permissions}
    expected = {"users:read", "users:create", "users:update"}
    assert permission_codenames == expected


@pytest.mark.asyncio
async def test_seed_defaults_creates_member_role_with_no_permissions(
    db_session: AsyncSession,
) -> None:
    """seed_defaults should create Member role with no permissions."""
    from groundwork.core.seed import seed_defaults

    await seed_defaults(db_session)

    result = await db_session.execute(
        select(Role)
        .where(Role.name == "Member")
        .options(selectinload(Role.permissions))
    )
    member_role = result.scalar_one()

    assert member_role.is_system is True
    assert member_role.description == "Standard member with basic access"
    assert len(member_role.permissions) == 0


@pytest.mark.asyncio
async def test_seed_defaults_creates_guest_role_with_no_permissions(
    db_session: AsyncSession,
) -> None:
    """seed_defaults should create Guest role with no permissions."""
    from groundwork.core.seed import seed_defaults

    await seed_defaults(db_session)

    result = await db_session.execute(
        select(Role).where(Role.name == "Guest").options(selectinload(Role.permissions))
    )
    guest_role = result.scalar_one()

    assert guest_role.is_system is True
    assert guest_role.description == "Guest with limited access"
    assert len(guest_role.permissions) == 0


@pytest.mark.asyncio
async def test_seed_defaults_is_idempotent_for_roles(
    db_session: AsyncSession,
) -> None:
    """seed_defaults should not duplicate roles when run multiple times."""
    from groundwork.core.seed import seed_defaults

    # Run twice
    await seed_defaults(db_session)
    await seed_defaults(db_session)

    # Count roles
    result = await db_session.execute(select(Role))
    roles = list(result.scalars().all())

    # Should have exactly 4 roles (no duplicates)
    assert len(roles) == 4


@pytest.mark.asyncio
async def test_seed_defaults_preserves_existing_roles(
    db_session: AsyncSession,
) -> None:
    """seed_defaults should not modify existing roles."""
    from groundwork.core.seed import seed_defaults

    # Create Admin role with different description
    existing_role = Role(
        name="Admin",
        description="Custom admin description",
        is_system=True,
    )
    db_session.add(existing_role)
    await db_session.flush()
    original_id = existing_role.id

    await seed_defaults(db_session)

    # Verify original role was not modified
    result = await db_session.execute(select(Role).where(Role.name == "Admin"))
    role = result.scalar_one()

    assert role.id == original_id
    # Description should be preserved (not overwritten)
    assert role.description == "Custom admin description"


@pytest.mark.asyncio
async def test_seed_defaults_adds_permissions_to_existing_admin_role(
    db_session: AsyncSession,
) -> None:
    """seed_defaults should add permissions to existing Admin role if missing."""
    from groundwork.core.seed import seed_defaults

    # Create Admin role without permissions (like setup wizard might have created)
    existing_role = Role(
        name="Admin",
        description="Administrator with full access",
        is_system=True,
    )
    db_session.add(existing_role)
    await db_session.flush()

    await seed_defaults(db_session)

    # Verify Admin role now has permissions
    result = await db_session.execute(
        select(Role).where(Role.name == "Admin").options(selectinload(Role.permissions))
    )
    admin_role = result.scalar_one()

    permission_codenames = {p.codename for p in admin_role.permissions}
    expected = {
        "users:create",
        "users:read",
        "users:update",
        "users:delete",
        "roles:manage",
        "settings:manage",
    }
    assert permission_codenames == expected


# =============================================================================
# All Roles System Flag
# =============================================================================


@pytest.mark.asyncio
async def test_seed_defaults_marks_all_roles_as_system(
    db_session: AsyncSession,
) -> None:
    """All default roles should have is_system=True."""
    from groundwork.core.seed import seed_defaults

    await seed_defaults(db_session)

    result = await db_session.execute(
        select(Role).where(Role.name.in_(["Admin", "Manager", "Member", "Guest"]))
    )
    roles = list(result.scalars().all())

    assert len(roles) == 4
    for role in roles:
        assert role.is_system is True, f"Role {role.name} should be a system role"


# =============================================================================
# App Lifespan Integration
# =============================================================================


@pytest.mark.asyncio
async def test_lifespan_calls_seed_defaults() -> None:
    """App lifespan should call seed_defaults during startup."""
    from unittest.mock import AsyncMock, patch

    from groundwork.main import create_app

    # Mock seed_defaults to track if it's called
    with patch("groundwork.main.seed_defaults", new_callable=AsyncMock) as mock_seed:
        app = create_app()

        # Manually trigger lifespan startup/shutdown
        async with app.router.lifespan_context(app):
            pass

        # Verify seed_defaults was called
        mock_seed.assert_called_once()
