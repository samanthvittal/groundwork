"""Issue management Pydantic schemas."""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from groundwork.issues.models import Priority, StatusCategory


# =============================================================================
# Issue Type Schemas
# =============================================================================


class IssueTypeResponse(BaseModel):
    """Response schema for issue type."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID | None
    name: str
    description: str | None
    icon: str
    color: str
    is_subtask: bool
    position: int


# =============================================================================
# Status Schemas
# =============================================================================


class StatusResponse(BaseModel):
    """Response schema for status."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID | None
    name: str
    description: str | None
    category: StatusCategory
    color: str
    position: int


# =============================================================================
# Label Schemas
# =============================================================================


class LabelCreate(BaseModel):
    """Request schema for creating a label."""

    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default="#6b7280", pattern=r"^#[0-9a-fA-F]{6}$")
    description: str | None = Field(default=None, max_length=200)


class LabelUpdate(BaseModel):
    """Request schema for updating a label."""

    name: str | None = Field(default=None, min_length=1, max_length=50)
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    description: str | None = Field(default=None, max_length=200)


class LabelResponse(BaseModel):
    """Response schema for label."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    description: str | None
    color: str
    created_at: datetime


# =============================================================================
# Issue Schemas
# =============================================================================


class IssueCreate(BaseModel):
    """Request schema for creating an issue."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    type_id: UUID
    status_id: UUID | None = None  # Defaults to first TODO status
    priority: Priority = Priority.MEDIUM
    assignee_id: UUID | None = None
    parent_id: UUID | None = None


class IssueUpdate(BaseModel):
    """Request schema for updating an issue."""

    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    type_id: UUID | None = None
    status_id: UUID | None = None
    priority: Priority | None = None
    assignee_id: UUID | None = None
    parent_id: UUID | None = None

    # Track which fields were explicitly set (including to None)
    model_config = ConfigDict(extra="forbid")


class IssueUserResponse(BaseModel):
    """Minimal user info for issue responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    first_name: str
    last_name: str
    display_name: str | None
    avatar_path: str | None

    @property
    def full_name(self) -> str:
        """Return user's full name."""
        return f"{self.first_name} {self.last_name}"


class IssueSummaryResponse(BaseModel):
    """Summary response for issue (used in lists)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key: str
    title: str
    priority: Priority
    type: IssueTypeResponse
    status: StatusResponse
    assignee: IssueUserResponse | None
    created_at: datetime
    updated_at: datetime


class IssueResponse(BaseModel):
    """Full response schema for issue."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    key: str
    issue_number: int
    title: str
    description: str | None
    priority: Priority
    type: IssueTypeResponse
    status: StatusResponse
    assignee: IssueUserResponse | None
    reporter: IssueUserResponse
    parent_id: UUID | None
    labels: list[LabelResponse]
    subtask_count: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class IssueDetailResponse(IssueResponse):
    """Detailed response with subtasks."""

    subtasks: list[IssueSummaryResponse] = []


# =============================================================================
# Subtask Schemas
# =============================================================================


class SubtaskCreate(BaseModel):
    """Request schema for creating a subtask."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    type_id: UUID
    priority: Priority = Priority.MEDIUM
    assignee_id: UUID | None = None


class SubtaskLink(BaseModel):
    """Request schema for linking an existing issue as subtask."""

    issue_id: UUID


# =============================================================================
# Label Assignment Schemas
# =============================================================================


class IssueLabelAdd(BaseModel):
    """Request schema for adding a label to an issue."""

    label_id: UUID


# =============================================================================
# Filter Schemas
# =============================================================================


class IssueFilters(BaseModel):
    """Query parameters for filtering issues."""

    status: str | None = None  # Comma-separated status IDs or category names
    type: str | None = None  # Comma-separated type IDs
    assignee: str | None = None  # "me", "unassigned", or user ID
    priority: str | None = None  # Comma-separated priorities
    label: UUID | None = None  # Single label ID
    parent: str | None = None  # "none" for root issues, or issue key
    q: str | None = None  # Search query
    sort: str = "-created_at"  # Sort field (prefix - for desc)
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=50, ge=1, le=100)
