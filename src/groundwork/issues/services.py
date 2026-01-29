"""Issue management services."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from groundwork.issues.models import (
    Issue,
    IssueLabel,
    IssueType,
    Label,
    Priority,
    Status,
    StatusCategory,
)
from groundwork.projects.models import Project, ProjectMember, ProjectRole


class IssueService:
    """Service for issue management operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    # =========================================================================
    # Issue CRUD
    # =========================================================================

    async def create_issue(
        self,
        project_id: UUID,
        title: str,
        type_id: UUID,
        reporter_id: UUID,
        status_id: UUID | None = None,
        priority: Priority = Priority.MEDIUM,
        description: str | None = None,
        assignee_id: UUID | None = None,
        parent_id: UUID | None = None,
    ) -> Issue:
        """Create a new issue.

        Args:
            project_id: Project to create issue in
            title: Issue title
            type_id: Issue type ID
            reporter_id: User ID of reporter
            status_id: Status ID (defaults to first TODO status)
            priority: Issue priority
            description: Issue description
            assignee_id: Assigned user ID
            parent_id: Parent issue ID for subtasks

        Returns:
            Created issue with relationships loaded
        """
        # Generate issue key
        key, issue_number = await self._generate_issue_key(project_id)

        # Get default status if not provided
        if status_id is None:
            status_id = await self._get_default_status_id(project_id)

        issue = Issue(
            project_id=project_id,
            key=key,
            issue_number=issue_number,
            title=title,
            description=description,
            type_id=type_id,
            status_id=status_id,
            priority=priority,
            assignee_id=assignee_id,
            reporter_id=reporter_id,
            parent_id=parent_id,
        )
        self.db.add(issue)
        await self.db.flush()

        # Expire parent's subtasks cache so subsequent loads reflect the new child
        if parent_id is not None:
            parent = await self.db.get(Issue, parent_id)
            if parent is not None:
                self.db.expire(parent, ["subtasks"])

        # Reload with relationships
        return await self.get_issue(issue.id)

    async def get_issue(self, issue_id: UUID) -> Issue | None:
        """Get issue by ID with relationships loaded."""
        result = await self.db.execute(
            select(Issue)
            .options(
                selectinload(Issue.project),
                selectinload(Issue.type),
                selectinload(Issue.status),
                selectinload(Issue.assignee),
                selectinload(Issue.reporter),
                selectinload(Issue.parent),
                selectinload(Issue.subtasks),
                selectinload(Issue.labels),
            )
            .where(Issue.id == issue_id)
        )
        return result.scalar_one_or_none()

    async def get_issue_by_key(self, key: str) -> Issue | None:
        """Get issue by key (e.g., 'PROJ-123') with relationships loaded."""
        result = await self.db.execute(
            select(Issue)
            .options(
                selectinload(Issue.project),
                selectinload(Issue.type),
                selectinload(Issue.status),
                selectinload(Issue.assignee),
                selectinload(Issue.reporter),
                selectinload(Issue.parent),
                selectinload(Issue.subtasks),
                selectinload(Issue.labels),
            )
            .where(Issue.key == key.upper())
        )
        return result.scalar_one_or_none()

    async def update_issue(
        self,
        issue_id: UUID,
        title: str | None = None,
        description: str | None = None,
        type_id: UUID | None = None,
        status_id: UUID | None = None,
        priority: Priority | None = None,
        assignee_id: UUID | None = ...,  # Use ... as sentinel for "not provided"
        parent_id: UUID | None = ...,
    ) -> Issue | None:
        """Update issue fields.

        Args:
            issue_id: Issue ID to update
            title: New title (if provided)
            description: New description (if provided)
            type_id: New type ID (if provided)
            status_id: New status ID (if provided)
            priority: New priority (if provided)
            assignee_id: New assignee ID (use None to unassign, ... to skip)
            parent_id: New parent ID (use None to remove parent, ... to skip)

        Returns:
            Updated issue or None if not found
        """
        issue = await self.get_issue(issue_id)
        if issue is None:
            return None

        if title is not None:
            issue.title = title
        if description is not None:
            issue.description = description
        if type_id is not None:
            issue.type_id = type_id
        if status_id is not None:
            issue.status_id = status_id
        if priority is not None:
            issue.priority = priority
        if assignee_id is not ...:
            issue.assignee_id = assignee_id
        if parent_id is not ...:
            issue.parent_id = parent_id

        await self.db.flush()
        return await self.get_issue(issue_id)

    async def delete_issue(self, issue_id: UUID) -> bool:
        """Soft delete an issue.

        Returns True if deleted, False if not found.
        """
        issue = await self.get_issue(issue_id)
        if issue is None:
            return False

        issue.deleted_at = datetime.utcnow()
        await self.db.flush()
        return True

    async def restore_issue(self, issue_id: UUID) -> Issue | None:
        """Restore a soft-deleted issue."""
        issue = await self.get_issue(issue_id)
        if issue is None:
            return None

        issue.deleted_at = None
        await self.db.flush()
        return await self.get_issue(issue_id)

    # =========================================================================
    # Issue Listing
    # =========================================================================

    async def list_issues(
        self,
        project_id: UUID,
        status_category: StatusCategory | None = None,
        status_id: UUID | None = None,
        type_id: UUID | None = None,
        assignee_id: UUID | None = None,
        priority: Priority | None = None,
        label_id: UUID | None = None,
        parent_id: UUID | None = ...,  # Use ... for "any", None for "no parent"
        search: str | None = None,
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Issue]:
        """List issues with filters.

        Args:
            project_id: Filter by project
            status_category: Filter by status category
            status_id: Filter by specific status
            type_id: Filter by issue type
            assignee_id: Filter by assignee (use None for unassigned)
            priority: Filter by priority
            label_id: Filter by label
            parent_id: Filter by parent (... for any, None for root issues only)
            search: Search in title and description
            include_deleted: Include soft-deleted issues
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of issues matching filters
        """
        query = (
            select(Issue)
            .options(
                selectinload(Issue.type),
                selectinload(Issue.status),
                selectinload(Issue.assignee),
                selectinload(Issue.labels),
            )
            .where(Issue.project_id == project_id)
        )

        # Filter by deleted status
        if not include_deleted:
            query = query.where(Issue.deleted_at.is_(None))

        # Filter by status category (requires join)
        if status_category is not None:
            query = query.join(Status).where(Status.category == status_category)

        # Filter by specific status
        if status_id is not None:
            query = query.where(Issue.status_id == status_id)

        # Filter by type
        if type_id is not None:
            query = query.where(Issue.type_id == type_id)

        # Filter by assignee
        if assignee_id is not None:
            query = query.where(Issue.assignee_id == assignee_id)

        # Filter by priority
        if priority is not None:
            query = query.where(Issue.priority == priority)

        # Filter by label (requires join)
        if label_id is not None:
            query = query.join(IssueLabel).where(IssueLabel.label_id == label_id)

        # Filter by parent
        if parent_id is not ...:
            if parent_id is None:
                query = query.where(Issue.parent_id.is_(None))
            else:
                query = query.where(Issue.parent_id == parent_id)

        # Search in title and description
        if search:
            search_term = f"%{search}%"
            query = query.where(
                Issue.title.ilike(search_term) | Issue.description.ilike(search_term)
            )

        # Order and paginate
        query = query.order_by(Issue.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_issues(
        self,
        project_id: UUID,
        include_deleted: bool = False,
    ) -> int:
        """Count issues in a project."""
        query = select(func.count(Issue.id)).where(Issue.project_id == project_id)

        if not include_deleted:
            query = query.where(Issue.deleted_at.is_(None))

        result = await self.db.execute(query)
        return result.scalar() or 0

    # =========================================================================
    # Status Management
    # =========================================================================

    async def change_status(
        self,
        issue_id: UUID,
        status_id: UUID,
    ) -> Issue | None:
        """Change issue status.

        Returns updated issue or None if not found.
        """
        return await self.update_issue(issue_id, status_id=status_id)

    # =========================================================================
    # Subtask Management
    # =========================================================================

    async def set_parent(
        self,
        issue_id: UUID,
        parent_id: UUID | None,
    ) -> Issue | None:
        """Set or remove parent issue (for subtasks).

        Args:
            issue_id: Issue to update
            parent_id: Parent issue ID, or None to remove parent

        Returns:
            Updated issue or None if not found
        """
        # Validate parent exists if provided
        if parent_id is not None:
            parent = await self.get_issue(parent_id)
            if parent is None:
                return None

            # Prevent circular references
            if parent_id == issue_id:
                return None

        return await self.update_issue(issue_id, parent_id=parent_id)

    async def list_subtasks(self, parent_id: UUID) -> list[Issue]:
        """List subtasks of an issue."""
        result = await self.db.execute(
            select(Issue)
            .options(
                selectinload(Issue.type),
                selectinload(Issue.status),
                selectinload(Issue.assignee),
            )
            .where(Issue.parent_id == parent_id, Issue.deleted_at.is_(None))
            .order_by(Issue.created_at)
        )
        return list(result.scalars().all())

    # =========================================================================
    # Label Management
    # =========================================================================

    async def add_label(self, issue_id: UUID, label_id: UUID) -> Issue | None:
        """Add a label to an issue.

        Returns updated issue or None if issue/label not found or already added.
        """
        issue = await self.get_issue(issue_id)
        if issue is None:
            return None

        # Check if label exists
        label = await self.db.get(Label, label_id)
        if label is None:
            return None

        # Check if already added
        existing = await self.db.execute(
            select(IssueLabel).where(
                IssueLabel.issue_id == issue_id,
                IssueLabel.label_id == label_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            return issue  # Already added, return as-is

        # Add label
        issue_label = IssueLabel(issue_id=issue_id, label_id=label_id)
        self.db.add(issue_label)
        await self.db.flush()

        # Expire cached labels so the next load picks up the new association
        self.db.expire(issue, ["labels"])
        return await self.get_issue(issue_id)

    async def remove_label(self, issue_id: UUID, label_id: UUID) -> Issue | None:
        """Remove a label from an issue.

        Returns updated issue or None if issue not found.
        """
        issue = await self.get_issue(issue_id)
        if issue is None:
            return None

        # Find and delete the association
        result = await self.db.execute(
            select(IssueLabel).where(
                IssueLabel.issue_id == issue_id,
                IssueLabel.label_id == label_id,
            )
        )
        issue_label = result.scalar_one_or_none()
        if issue_label is not None:
            await self.db.delete(issue_label)
            await self.db.flush()
            # Expire cached labels so the next load reflects the removal
            self.db.expire(issue, ["labels"])

        return await self.get_issue(issue_id)

    # =========================================================================
    # Permission Checks
    # =========================================================================

    async def user_can_view(self, issue_id: UUID, user_id: UUID) -> bool:
        """Check if user can view an issue (project VIEWER+ role)."""
        issue = await self.get_issue(issue_id)
        if issue is None:
            return False

        return await self._user_has_project_access(issue.project_id, user_id)

    async def user_can_edit(self, issue_id: UUID, user_id: UUID) -> bool:
        """Check if user can edit an issue (project MEMBER+ role or assignee)."""
        issue = await self.get_issue(issue_id)
        if issue is None:
            return False

        # Assignee can edit
        if issue.assignee_id == user_id:
            return True

        # Check project membership
        member = await self._get_project_member(issue.project_id, user_id)
        if member is None:
            return False

        return member.role in (
            ProjectRole.OWNER,
            ProjectRole.ADMIN,
            ProjectRole.MEMBER,
        )

    async def user_can_delete(self, issue_id: UUID, user_id: UUID) -> bool:
        """Check if user can delete an issue (project ADMIN+ role)."""
        issue = await self.get_issue(issue_id)
        if issue is None:
            return False

        member = await self._get_project_member(issue.project_id, user_id)
        if member is None:
            return False

        return member.role in (ProjectRole.OWNER, ProjectRole.ADMIN)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _generate_issue_key(self, project_id: UUID) -> tuple[str, int]:
        """Generate next issue key for project with locking.

        Uses row-level locking on the project to serialize key generation.

        Returns:
            Tuple of (key, issue_number)
        """
        # Lock the project row to serialize concurrent issue creation
        result = await self.db.execute(
            select(Project).where(Project.id == project_id).with_for_update()
        )
        project = result.scalar_one()

        # Now safely get the max issue number
        result = await self.db.execute(
            select(func.coalesce(func.max(Issue.issue_number), 0))
            .where(Issue.project_id == project_id)
        )
        max_number = result.scalar() or 0
        next_number = max_number + 1

        key = f"{project.key}-{next_number}"
        return key, next_number

    async def _get_default_status_id(self, project_id: UUID) -> UUID:
        """Get default status ID (first TODO status)."""
        # First try project-specific status
        result = await self.db.execute(
            select(Status)
            .where(
                Status.project_id == project_id,
                Status.category == StatusCategory.TODO,
            )
            .order_by(Status.position)
            .limit(1)
        )
        status = result.scalar_one_or_none()

        if status is None:
            # Fall back to system default
            result = await self.db.execute(
                select(Status)
                .where(
                    Status.project_id.is_(None),
                    Status.category == StatusCategory.TODO,
                )
                .order_by(Status.position)
                .limit(1)
            )
            status = result.scalar_one_or_none()

        if status is None:
            raise ValueError("No default TODO status found")

        return status.id

    async def _user_has_project_access(self, project_id: UUID, user_id: UUID) -> bool:
        """Check if user has any access to a project."""
        member = await self._get_project_member(project_id, user_id)
        return member is not None

    async def _get_project_member(
        self, project_id: UUID, user_id: UUID
    ) -> ProjectMember | None:
        """Get project membership for user."""
        result = await self.db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()


class LabelService:
    """Service for label management operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    async def create_label(
        self,
        project_id: UUID,
        name: str,
        color: str = "#6b7280",
        description: str | None = None,
    ) -> Label | None:
        """Create a new label.

        Returns created label or None if name already exists in project.
        """
        # Check for duplicate name
        existing = await self.db.execute(
            select(Label).where(
                Label.project_id == project_id,
                Label.name == name,
            )
        )
        if existing.scalar_one_or_none() is not None:
            return None

        label = Label(
            project_id=project_id,
            name=name,
            color=color,
            description=description,
        )
        self.db.add(label)
        await self.db.flush()

        return label

    async def get_label(self, label_id: UUID) -> Label | None:
        """Get label by ID."""
        return await self.db.get(Label, label_id)

    async def update_label(
        self,
        label_id: UUID,
        name: str | None = None,
        color: str | None = None,
        description: str | None = None,
    ) -> Label | None:
        """Update label fields.

        Returns updated label or None if not found.
        """
        label = await self.get_label(label_id)
        if label is None:
            return None

        if name is not None:
            # Check for duplicate name
            existing = await self.db.execute(
                select(Label).where(
                    Label.project_id == label.project_id,
                    Label.name == name,
                    Label.id != label_id,
                )
            )
            if existing.scalar_one_or_none() is not None:
                return None  # Name conflict

            label.name = name

        if color is not None:
            label.color = color
        if description is not None:
            label.description = description

        await self.db.flush()
        return label

    async def delete_label(self, label_id: UUID) -> bool:
        """Delete a label.

        Returns True if deleted, False if not found.
        """
        label = await self.get_label(label_id)
        if label is None:
            return False

        await self.db.delete(label)
        await self.db.flush()
        return True

    async def list_labels(self, project_id: UUID) -> list[Label]:
        """List all labels in a project."""
        result = await self.db.execute(
            select(Label)
            .where(Label.project_id == project_id)
            .order_by(Label.name)
        )
        return list(result.scalars().all())


class IssueTypeService:
    """Service for issue type operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    async def list_issue_types(self, project_id: UUID | None = None) -> list[IssueType]:
        """List issue types for a project (including system defaults).

        Args:
            project_id: Project ID to get types for, or None for system types only

        Returns:
            List of issue types (project-specific + system defaults)
        """
        if project_id is not None:
            # Get both project-specific and system types
            result = await self.db.execute(
                select(IssueType)
                .where(
                    (IssueType.project_id == project_id)
                    | (IssueType.project_id.is_(None))
                )
                .order_by(IssueType.position)
            )
        else:
            # System types only
            result = await self.db.execute(
                select(IssueType)
                .where(IssueType.project_id.is_(None))
                .order_by(IssueType.position)
            )

        return list(result.scalars().all())

    async def get_issue_type(self, type_id: UUID) -> IssueType | None:
        """Get issue type by ID."""
        return await self.db.get(IssueType, type_id)


class StatusService:
    """Service for status operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    async def list_statuses(self, project_id: UUID | None = None) -> list[Status]:
        """List statuses for a project (including system defaults).

        Args:
            project_id: Project ID to get statuses for, or None for system types only

        Returns:
            List of statuses (project-specific + system defaults)
        """
        if project_id is not None:
            # Get both project-specific and system statuses
            result = await self.db.execute(
                select(Status)
                .where(
                    (Status.project_id == project_id) | (Status.project_id.is_(None))
                )
                .order_by(Status.position)
            )
        else:
            # System statuses only
            result = await self.db.execute(
                select(Status)
                .where(Status.project_id.is_(None))
                .order_by(Status.position)
            )

        return list(result.scalars().all())

    async def get_status(self, status_id: UUID) -> Status | None:
        """Get status by ID."""
        return await self.db.get(Status, status_id)
