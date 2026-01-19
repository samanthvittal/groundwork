"""Project models."""

from datetime import datetime
from enum import Enum
from uuid import UUID as PythonUUID
from uuid import uuid4

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from groundwork.core.database import Base


class ProjectStatus(str, Enum):
    """Project lifecycle status."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ProjectVisibility(str, Enum):
    """Project visibility level."""

    PRIVATE = "private"  # Only members can see
    INTERNAL = "internal"  # All logged-in users can see
    PUBLIC = "public"  # Anyone can see (future use)


class ProjectRole(str, Enum):
    """Role within a project."""

    OWNER = "owner"  # Full control, can delete project
    ADMIN = "admin"  # Can manage members and settings
    MEMBER = "member"  # Can create/edit issues
    VIEWER = "viewer"  # Read-only access


class Project(Base):
    """Project for organizing issues and team work."""

    __tablename__ = "projects"

    id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    key: Mapped[str] = mapped_column(
        String(10), unique=True, index=True
    )  # e.g., "PROJ", "WEB"
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[ProjectVisibility] = mapped_column(
        default=ProjectVisibility.PRIVATE
    )
    status: Mapped[ProjectStatus] = mapped_column(default=ProjectStatus.ACTIVE)
    owner_id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("users.id")
    )
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )
    archived_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="owned_projects")
    members: Mapped[list["ProjectMember"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    @property
    def member_count(self) -> int:
        """Return number of members in project."""
        return len(self.members) if self.members else 0


class ProjectMember(Base):
    """Association between users and projects with role."""

    __tablename__ = "project_members"

    id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE")
    )
    user_id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    role: Mapped[ProjectRole] = mapped_column(default=ProjectRole.MEMBER)
    joined_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="project_memberships")

    # Unique constraint: user can only be member once per project
    __table_args__ = (
        UniqueConstraint(
            "project_id", "user_id", name="uq_project_members_project_user"
        ),
        {"comment": "Project membership with role"},
    )


# Import User at runtime to avoid circular imports
from groundwork.auth.models import User  # noqa: E402, F401
