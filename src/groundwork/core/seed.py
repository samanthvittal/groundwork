"""Default roles and permissions seeding."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from groundwork.auth.models import Permission, Role
from groundwork.core.logging import get_logger
from groundwork.issues.seed import seed_issue_defaults

logger = get_logger(__name__)

# Default permissions with their descriptions
DEFAULT_PERMISSIONS: list[tuple[str, str]] = [
    ("users:create", "Create new users"),
    ("users:read", "View user list and details"),
    ("users:update", "Edit user profiles and roles"),
    ("users:delete", "Deactivate/delete users"),
    ("roles:manage", "Create, edit, delete custom roles"),
    ("settings:manage", "Modify instance settings, SMTP config"),
]

# Default roles with their permissions
# Format: (name, description, list of permission codenames)
DEFAULT_ROLES: list[tuple[str, str, list[str]]] = [
    (
        "Admin",
        "Administrator with full access",
        [
            "users:create",
            "users:read",
            "users:update",
            "users:delete",
            "roles:manage",
            "settings:manage",
        ],
    ),
    (
        "Manager",
        "Manager with user management access",
        ["users:read", "users:create", "users:update"],
    ),
    ("Member", "Standard member with basic access", []),
    ("Guest", "Guest with limited access", []),
]


async def seed_defaults(db: AsyncSession) -> None:
    """Seed default permissions and roles.

    This function is idempotent - it's safe to run multiple times.
    It will:
    - Create permissions that don't exist
    - Create roles that don't exist
    - Add missing permissions to existing roles
    - Mark all default roles as system roles

    Args:
        db: Database session to use for seeding.
    """
    # Create permissions first
    permissions_map = await _seed_permissions(db)

    # Then create roles with their permissions
    await _seed_roles(db, permissions_map)

    # Seed issue types and statuses
    await seed_issue_defaults(db)

    await db.flush()
    logger.info("Default roles and permissions seeded successfully")


async def _seed_permissions(db: AsyncSession) -> dict[str, Permission]:
    """Create default permissions if they don't exist.

    Args:
        db: Database session.

    Returns:
        Dict mapping permission codenames to Permission objects.
    """
    permissions_map: dict[str, Permission] = {}

    for codename, description in DEFAULT_PERMISSIONS:
        # Check if permission already exists
        result = await db.execute(
            select(Permission).where(Permission.codename == codename)
        )
        permission = result.scalar_one_or_none()

        if permission is None:
            # Create new permission
            permission = Permission(codename=codename, description=description)
            db.add(permission)
            logger.debug(f"Created permission: {codename}")

        permissions_map[codename] = permission

    await db.flush()
    return permissions_map


async def _seed_roles(db: AsyncSession, permissions_map: dict[str, Permission]) -> None:
    """Create default roles if they don't exist.

    Args:
        db: Database session.
        permissions_map: Dict mapping permission codenames to Permission objects.
    """
    for name, description, permission_codenames in DEFAULT_ROLES:
        # Check if role already exists
        result = await db.execute(
            select(Role)
            .where(Role.name == name)
            .options(selectinload(Role.permissions))
        )
        role = result.scalar_one_or_none()

        if role is None:
            # Create new role with permissions
            role_permissions = [
                permissions_map[codename]
                for codename in permission_codenames
                if codename in permissions_map
            ]
            role = Role(
                name=name,
                description=description,
                is_system=True,
                permissions=role_permissions,
            )
            db.add(role)
            logger.debug(f"Created role: {name}")
        else:
            # Role exists - add any missing permissions
            existing_codenames = {p.codename for p in role.permissions}
            for codename in permission_codenames:
                if codename not in existing_codenames and codename in permissions_map:
                    role.permissions.append(permissions_map[codename])
                    logger.debug(f"Added permission {codename} to role {name}")

    await db.flush()
