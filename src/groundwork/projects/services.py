"""Project management service."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from groundwork.projects.models import (
    Project,
    ProjectMember,
    ProjectRole,
    ProjectStatus,
    ProjectVisibility,
)


class ProjectService:
    """Service for project management operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    async def list_projects(
        self,
        skip: int = 0,
        limit: int = 100,
        status: ProjectStatus | None = None,
    ) -> list[Project]:
        """List projects with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by project status (optional)
        """
        query = select(Project).options(selectinload(Project.members))

        if status is not None:
            query = query.where(Project.status == status)

        query = query.offset(skip).limit(limit).order_by(Project.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_user_projects(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Project]:
        """List projects where user is owner or member."""
        # Get projects where user is owner
        owned_query = select(Project).where(Project.owner_id == user_id)

        # Get projects where user is member
        member_query = (
            select(Project)
            .join(ProjectMember, Project.id == ProjectMember.project_id)
            .where(ProjectMember.user_id == user_id)
        )

        # Union and deduplicate
        combined = owned_query.union(member_query)
        final_query = (
            select(Project)
            .where(Project.id.in_(select(combined.subquery().c.id)))
            .options(selectinload(Project.members))
            .offset(skip)
            .limit(limit)
            .order_by(Project.created_at.desc())
        )

        result = await self.db.execute(final_query)
        return list(result.scalars().all())

    async def get_project(self, project_id: UUID) -> Project | None:
        """Get project by ID with members loaded."""
        result = await self.db.execute(
            select(Project)
            .options(selectinload(Project.members).selectinload(ProjectMember.user))
            .where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def get_project_by_key(self, key: str) -> Project | None:
        """Get project by key with members loaded."""
        result = await self.db.execute(
            select(Project)
            .options(selectinload(Project.members).selectinload(ProjectMember.user))
            .where(Project.key == key)
        )
        return result.scalar_one_or_none()

    async def create_project(
        self,
        key: str,
        name: str,
        owner_id: UUID,
        description: str | None = None,
        visibility: ProjectVisibility = ProjectVisibility.PRIVATE,
    ) -> Project | None:
        """Create a new project.

        Returns the created project, or None if key already exists.
        The owner is automatically added as a member with OWNER role.
        """
        # Check if key already exists
        existing = await self.db.execute(select(Project).where(Project.key == key))
        if existing.scalar_one_or_none() is not None:
            return None

        project = Project(
            key=key.upper(),
            name=name,
            description=description,
            visibility=visibility,
            status=ProjectStatus.ACTIVE,
            owner_id=owner_id,
        )
        self.db.add(project)
        await self.db.flush()

        # Add owner as member with OWNER role
        owner_member = ProjectMember(
            project_id=project.id,
            user_id=owner_id,
            role=ProjectRole.OWNER,
        )
        self.db.add(owner_member)
        await self.db.flush()

        # Reload with relationships
        return await self.get_project(project.id)

    async def update_project(
        self,
        project_id: UUID,
        name: str | None = None,
        description: str | None = None,
        visibility: ProjectVisibility | None = None,
        status: ProjectStatus | None = None,
    ) -> Project | None:
        """Update project fields.

        Returns updated project, or None if project not found.
        Only provided (non-None) fields are updated.
        """
        project = await self.get_project(project_id)
        if project is None:
            return None

        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if visibility is not None:
            project.visibility = visibility
        if status is not None:
            project.status = status
            if status == ProjectStatus.ARCHIVED:
                project.archived_at = datetime.utcnow()
            elif project.archived_at is not None:
                project.archived_at = None

        await self.db.flush()
        return await self.get_project(project_id)

    async def archive_project(self, project_id: UUID) -> Project | None:
        """Archive a project."""
        return await self.update_project(project_id, status=ProjectStatus.ARCHIVED)

    async def delete_project(self, project_id: UUID) -> bool:
        """Soft delete a project.

        Returns True if project was deleted, False if not found.
        """
        project = await self.get_project(project_id)
        if project is None:
            return False

        project.status = ProjectStatus.DELETED
        await self.db.flush()
        return True

    # Member management

    async def get_member(self, project_id: UUID, user_id: UUID) -> ProjectMember | None:
        """Get project member by project and user ID."""
        result = await self.db.execute(
            select(ProjectMember)
            .options(selectinload(ProjectMember.user))
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def add_member(
        self,
        project_id: UUID,
        user_id: UUID,
        role: ProjectRole = ProjectRole.MEMBER,
    ) -> ProjectMember | None:
        """Add a member to a project.

        Returns the created member, or None if user is already a member.
        """
        # Check if already a member
        existing = await self.get_member(project_id, user_id)
        if existing is not None:
            return None

        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role,
        )
        self.db.add(member)
        await self.db.flush()

        return await self.get_member(project_id, user_id)

    async def update_member_role(
        self,
        project_id: UUID,
        user_id: UUID,
        role: ProjectRole,
    ) -> ProjectMember | None:
        """Update a member's role.

        Returns updated member, or None if member not found.
        """
        member = await self.get_member(project_id, user_id)
        if member is None:
            return None

        member.role = role
        await self.db.flush()
        return member

    async def remove_member(self, project_id: UUID, user_id: UUID) -> bool:
        """Remove a member from a project.

        Returns True if member was removed, False if not found.
        """
        member = await self.get_member(project_id, user_id)
        if member is None:
            return False

        await self.db.delete(member)
        await self.db.flush()
        return True

    async def list_project_members(self, project_id: UUID) -> list[ProjectMember]:
        """List all members of a project."""
        result = await self.db.execute(
            select(ProjectMember)
            .options(selectinload(ProjectMember.user))
            .where(ProjectMember.project_id == project_id)
            .order_by(ProjectMember.joined_at)
        )
        return list(result.scalars().all())

    # Permission checks

    async def user_can_access(self, project_id: UUID, user_id: UUID) -> bool:
        """Check if user can access a project (view)."""
        project = await self.get_project(project_id)
        if project is None:
            return False

        # Owner can always access
        if project.owner_id == user_id:
            return True

        # Check visibility
        if project.visibility == ProjectVisibility.PUBLIC:
            return True

        if project.visibility == ProjectVisibility.INTERNAL:
            # Any logged-in user can access internal projects
            return True

        # Private projects: check membership
        member = await self.get_member(project_id, user_id)
        return member is not None

    async def user_can_edit(self, project_id: UUID, user_id: UUID) -> bool:
        """Check if user can edit a project."""
        member = await self.get_member(project_id, user_id)
        if member is None:
            return False

        return member.role in (ProjectRole.OWNER, ProjectRole.ADMIN, ProjectRole.MEMBER)

    async def user_can_admin(self, project_id: UUID, user_id: UUID) -> bool:
        """Check if user can administer a project (manage members, settings)."""
        member = await self.get_member(project_id, user_id)
        if member is None:
            return False

        return member.role in (ProjectRole.OWNER, ProjectRole.ADMIN)

    async def user_is_owner(self, project_id: UUID, user_id: UUID) -> bool:
        """Check if user is the project owner."""
        project = await self.get_project(project_id)
        if project is None:
            return False

        return project.owner_id == user_id
