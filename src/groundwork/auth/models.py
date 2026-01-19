"""Authentication models."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID as PythonUUID
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from groundwork.core.database import Base

if TYPE_CHECKING:
    from groundwork.projects.models import Project, ProjectMember

# Association table for Role <-> Permission many-to-many
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id", PostgresUUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True
    ),
    Column(
        "permission_id",
        PostgresUUID(as_uuid=True),
        ForeignKey("permissions.id"),
        primary_key=True,
    ),
)


class Permission(Base):
    """System permission."""

    __tablename__ = "permissions"

    id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    codename: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(500))

    roles: Mapped[list["Role"]] = relationship(
        secondary=role_permissions, back_populates="permissions"
    )


class Role(Base):
    """User role with permissions."""

    __tablename__ = "roles"

    id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(String(500))
    is_system: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    users: Mapped[list["User"]] = relationship(back_populates="role")
    permissions: Mapped[list["Permission"]] = relationship(
        secondary=role_permissions, back_populates="roles"
    )

    def has_permission(self, codename: str) -> bool:
        """Check if role has a specific permission."""
        return any(p.codename == codename for p in self.permissions)


class User(Base):
    """Application user."""

    __tablename__ = "users"

    id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    avatar_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    email_verified: Mapped[bool] = mapped_column(default=False)
    role_id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("roles.id")
    )
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    language: Mapped[str] = mapped_column(String(10), default="en")
    theme: Mapped[str] = mapped_column(String(20), default="system")
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    role: Mapped["Role"] = relationship(back_populates="users")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")
    owned_projects: Mapped[list["Project"]] = relationship(back_populates="owner")
    project_memberships: Mapped[list["ProjectMember"]] = relationship(
        back_populates="user"
    )

    @property
    def full_name(self) -> str:
        """Return user's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role is not None and self.role.name == "Admin"

    @property
    def avatar_url(self) -> str | None:
        """Return the avatar URL if avatar_path is set."""
        if self.avatar_path:
            return f"/static/avatars/{self.avatar_path}"
        return None


class RefreshToken(Base):
    """Refresh token for session management."""

    __tablename__ = "refresh_tokens"

    id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


class PasswordResetToken(Base):
    """Password reset token.

    Uses selector+validator pattern to prevent timing attacks:
    - token_selector: stored unhashed, used for O(1) lookup
    - token_hash: hash of the validator portion only
    - Full token format: {selector}.{validator}
    """

    __tablename__ = "password_reset_tokens"

    id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    token_selector: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    token_hash: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    user: Mapped["User"] = relationship()
