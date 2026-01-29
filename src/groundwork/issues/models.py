"""Issue management models."""

from datetime import datetime
from enum import Enum
from uuid import UUID as PythonUUID
from uuid import uuid4

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from groundwork.core.database import Base


class StatusCategory(str, Enum):
    """Category for grouping statuses."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class Priority(str, Enum):
    """Issue priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class IssueType(Base):
    """Issue type definition (Task, Bug, Story, Epic, etc.)."""

    __tablename__ = "issue_types"

    id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[PythonUUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
    )  # NULL = system default
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    icon: Mapped[str] = mapped_column(String(50), default="task")  # icon identifier
    color: Mapped[str] = mapped_column(String(7), default="#3b82f6")  # hex color
    is_subtask: Mapped[bool] = mapped_column(default=True)  # can be a subtask?
    position: Mapped[int] = mapped_column(default=0)  # display order
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    project: Mapped["Project | None"] = relationship()
    issues: Mapped[list["Issue"]] = relationship(back_populates="type")

    __table_args__ = (
        Index("ix_issue_types_project_id", "project_id"),
        {"comment": "Issue type definitions"},
    )


class Status(Base):
    """Issue status definition (To Do, In Progress, Done, etc.)."""

    __tablename__ = "statuses"

    id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[PythonUUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
    )  # NULL = system default
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    category: Mapped[StatusCategory] = mapped_column(default=StatusCategory.TODO)
    color: Mapped[str] = mapped_column(String(7), default="#6b7280")  # hex color
    position: Mapped[int] = mapped_column(default=0)  # display order
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    project: Mapped["Project | None"] = relationship()
    issues: Mapped[list["Issue"]] = relationship(back_populates="status")

    __table_args__ = (
        Index("ix_statuses_project_id", "project_id"),
        {"comment": "Issue status definitions"},
    )


class Label(Base):
    """Project label for categorizing issues."""

    __tablename__ = "labels"

    id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
    )
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    color: Mapped[str] = mapped_column(String(7), default="#6b7280")  # hex color
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    project: Mapped["Project"] = relationship()
    issues: Mapped[list["Issue"]] = relationship(
        secondary="issue_labels", back_populates="labels"
    )

    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_labels_project_name"),
        Index("ix_labels_project_id", "project_id"),
        {"comment": "Project labels for categorizing issues"},
    )


class Issue(Base):
    """Core issue entity for tracking work."""

    __tablename__ = "issues"

    id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
    )
    key: Mapped[str] = mapped_column(
        String(20), unique=True, index=True
    )  # e.g., "PROJ-123"
    issue_number: Mapped[int] = mapped_column()  # auto-increment per project
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Type and Status
    type_id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("issue_types.id"),
    )
    status_id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("statuses.id"),
    )
    priority: Mapped[Priority] = mapped_column(default=Priority.MEDIUM)

    # People
    assignee_id: Mapped[PythonUUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reporter_id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id"),
    )

    # Hierarchy (subtasks)
    parent_id: Mapped[PythonUUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("issues.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)  # soft delete

    # Relationships
    project: Mapped["Project"] = relationship()
    type: Mapped["IssueType"] = relationship(back_populates="issues")
    status: Mapped["Status"] = relationship(back_populates="issues")
    assignee: Mapped["User | None"] = relationship(
        foreign_keys=[assignee_id], back_populates="assigned_issues"
    )
    reporter: Mapped["User"] = relationship(
        foreign_keys=[reporter_id], back_populates="reported_issues"
    )
    parent: Mapped["Issue | None"] = relationship(
        back_populates="subtasks", remote_side=[id]
    )
    subtasks: Mapped[list["Issue"]] = relationship(back_populates="parent")
    labels: Mapped[list["Label"]] = relationship(
        secondary="issue_labels", back_populates="issues"
    )

    @property
    def is_deleted(self) -> bool:
        """Check if issue is soft deleted."""
        return self.deleted_at is not None

    @property
    def subtask_count(self) -> int:
        """Return number of subtasks."""
        return len(self.subtasks) if self.subtasks else 0

    __table_args__ = (
        UniqueConstraint("project_id", "issue_number", name="uq_issues_project_number"),
        Index("ix_issues_project_id", "project_id"),
        Index("ix_issues_status_id", "status_id"),
        Index("ix_issues_type_id", "type_id"),
        Index("ix_issues_assignee_id", "assignee_id"),
        Index("ix_issues_parent_id", "parent_id"),
        Index("ix_issues_deleted_at", "deleted_at"),
        {"comment": "Issues for tracking work"},
    )


class IssueLabel(Base):
    """Association between issues and labels."""

    __tablename__ = "issue_labels"

    issue_id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("issues.id", ondelete="CASCADE"),
        primary_key=True,
    )
    label_id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("labels.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    __table_args__ = ({"comment": "Issue-label associations"},)


# Import at runtime to avoid circular imports
from groundwork.auth.models import User  # noqa: E402, F401
from groundwork.projects.models import Project  # noqa: E402, F401
