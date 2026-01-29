"""Default issue types and statuses seeding."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.core.logging import get_logger
from groundwork.issues.models import IssueType, Status, StatusCategory

logger = get_logger(__name__)

# Default issue types (system-wide, project_id=NULL)
# Format: (name, description, icon, color, is_subtask, position)
DEFAULT_ISSUE_TYPES: list[tuple[str, str, str, str, bool, int]] = [
    ("Epic", "Large feature or initiative", "epic", "#8b5cf6", False, 0),
    ("Story", "User-facing feature or requirement", "story", "#22c55e", False, 1),
    ("Task", "Work item or to-do", "task", "#3b82f6", True, 2),
    ("Bug", "Defect or issue to fix", "bug", "#ef4444", True, 3),
]

# Default statuses (system-wide, project_id=NULL)
# Format: (name, description, category, color, position)
DEFAULT_STATUSES: list[tuple[str, str, StatusCategory, str, int]] = [
    ("To Do", "Work not yet started", StatusCategory.TODO, "#6b7280", 0),
    ("In Progress", "Work currently being done", StatusCategory.IN_PROGRESS, "#3b82f6", 1),
    ("In Review", "Work awaiting review", StatusCategory.IN_PROGRESS, "#f59e0b", 2),
    ("Done", "Work completed", StatusCategory.DONE, "#22c55e", 3),
]


async def seed_issue_defaults(db: AsyncSession) -> None:
    """Seed default issue types and statuses.

    This function is idempotent - it's safe to run multiple times.
    It creates system-wide defaults (project_id=NULL) that apply to all projects.

    Args:
        db: Database session to use for seeding.
    """
    await _seed_issue_types(db)
    await _seed_statuses(db)
    await db.flush()
    logger.info("Default issue types and statuses seeded successfully")


async def _seed_issue_types(db: AsyncSession) -> None:
    """Create default issue types if they don't exist.

    Args:
        db: Database session.
    """
    for name, description, icon, color, is_subtask, position in DEFAULT_ISSUE_TYPES:
        # Check if type already exists (system-wide, no project_id)
        result = await db.execute(
            select(IssueType).where(
                IssueType.name == name,
                IssueType.project_id.is_(None),
            )
        )
        issue_type = result.scalar_one_or_none()

        if issue_type is None:
            issue_type = IssueType(
                project_id=None,
                name=name,
                description=description,
                icon=icon,
                color=color,
                is_subtask=is_subtask,
                position=position,
            )
            db.add(issue_type)
            logger.debug(f"Created issue type: {name}")


async def _seed_statuses(db: AsyncSession) -> None:
    """Create default statuses if they don't exist.

    Args:
        db: Database session.
    """
    for name, description, category, color, position in DEFAULT_STATUSES:
        # Check if status already exists (system-wide, no project_id)
        result = await db.execute(
            select(Status).where(
                Status.name == name,
                Status.project_id.is_(None),
            )
        )
        status = result.scalar_one_or_none()

        if status is None:
            status = Status(
                project_id=None,
                name=name,
                description=description,
                category=category,
                color=color,
                position=position,
            )
            db.add(status)
            logger.debug(f"Created status: {name}")
