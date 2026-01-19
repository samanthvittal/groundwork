"""Role management service."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from groundwork.auth.models import Permission, Role


class RoleService:
    """Service for role management operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    async def list_roles(self) -> list[Role]:
        """List all roles."""
        result = await self.db.execute(
            select(Role).options(selectinload(Role.permissions)).order_by(Role.name)
        )
        return list(result.scalars().all())

    async def get_role(self, role_id: UUID) -> Role | None:
        """Get role by ID with permissions loaded."""
        result = await self.db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )
        return result.scalar_one_or_none()

    async def create_role(
        self,
        name: str,
        description: str,
        permission_ids: list[UUID],
    ) -> Role | None:
        """Create a new role.

        Returns the created role, or None if name already exists.
        """
        # Check if name already exists
        existing = await self.db.execute(select(Role).where(Role.name == name))
        if existing.scalar_one_or_none() is not None:
            return None

        # Create role
        role = Role(
            name=name,
            description=description,
            is_system=False,
        )

        # Add permissions if provided
        if permission_ids:
            perm_result = await self.db.execute(
                select(Permission).where(Permission.id.in_(permission_ids))
            )
            permissions = list(perm_result.scalars().all())
            role.permissions = permissions

        self.db.add(role)
        await self.db.flush()

        # Reload with permissions relationship
        return await self.get_role(role.id)

    async def update_role(
        self,
        role_id: UUID,
        name: str | None = None,
        description: str | None = None,
        permission_ids: list[UUID] | None = None,
    ) -> Role | None | str:
        """Update role fields.

        Returns:
            Updated role if successful
            None if role not found
            "duplicate" if name already exists on another role
        Only provided (non-None) fields are updated.
        """
        role = await self.get_role(role_id)
        if role is None:
            return None

        if name is not None and name != role.name:
            # Check if new name already exists on another role
            existing = await self.db.execute(
                select(Role).where(Role.name == name).where(Role.id != role_id)
            )
            if existing.scalar_one_or_none() is not None:
                return "duplicate"
            role.name = name
        elif name is not None:
            role.name = name
        if description is not None:
            role.description = description
        if permission_ids is not None:
            # Replace permissions
            perm_result = await self.db.execute(
                select(Permission).where(Permission.id.in_(permission_ids))
            )
            permissions = list(perm_result.scalars().all())
            role.permissions = permissions

        await self.db.flush()

        # Reload with permissions
        return await self.get_role(role_id)

    async def delete_role(self, role_id: UUID) -> bool | str:
        """Delete a role.

        Returns:
            True if role was deleted successfully
            False if role not found
            "system" if role is a system role and cannot be deleted
        """
        role = await self.get_role(role_id)
        if role is None:
            return False

        if role.is_system:
            return "system"

        await self.db.delete(role)
        await self.db.flush()
        return True

    async def list_permissions(self) -> list[Permission]:
        """List all permissions."""
        result = await self.db.execute(select(Permission).order_by(Permission.codename))
        return list(result.scalars().all())
