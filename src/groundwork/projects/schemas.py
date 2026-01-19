"""Project management Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from groundwork.projects.models import ProjectRole, ProjectStatus, ProjectVisibility


# Request schemas
class ProjectCreate(BaseModel):
    """Create project request."""

    key: str = Field(min_length=2, max_length=10, pattern=r"^[A-Z][A-Z0-9]*$")
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    visibility: ProjectVisibility = ProjectVisibility.PRIVATE


class ProjectUpdate(BaseModel):
    """Update project request - all fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    visibility: ProjectVisibility | None = None
    status: ProjectStatus | None = None


class ProjectMemberAdd(BaseModel):
    """Add member to project request."""

    user_id: UUID
    role: ProjectRole = ProjectRole.MEMBER


class ProjectMemberUpdate(BaseModel):
    """Update project member role."""

    role: ProjectRole


# Response schemas
class ProjectMemberResponse(BaseModel):
    """Project member response."""

    id: UUID
    user_id: UUID
    role: ProjectRole
    joined_at: datetime

    model_config = {"from_attributes": True}


class ProjectMemberDetailResponse(ProjectMemberResponse):
    """Project member with user details."""

    user_email: str | None = None
    user_name: str | None = None


class ProjectResponse(BaseModel):
    """Project response model (list view)."""

    id: UUID
    key: str
    name: str
    description: str | None
    visibility: ProjectVisibility
    status: ProjectStatus
    owner_id: UUID
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    member_count: int = 0

    model_config = {"from_attributes": True}


class ProjectDetailResponse(ProjectResponse):
    """Project response with members (detail view)."""

    members: list[ProjectMemberResponse] = []
