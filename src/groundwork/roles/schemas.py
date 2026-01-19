"""Role management Pydantic schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


# Request schemas
class RoleCreate(BaseModel):
    """Create role request."""

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    permission_ids: list[UUID] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    """Update role request - all fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    permission_ids: list[UUID] | None = None


# Response schemas
class PermissionResponse(BaseModel):
    """Permission response model."""

    id: UUID
    codename: str
    description: str

    model_config = {"from_attributes": True}


class RoleResponse(BaseModel):
    """Role response model (list view)."""

    id: UUID
    name: str
    description: str
    is_system: bool

    model_config = {"from_attributes": True}


class RoleDetailResponse(RoleResponse):
    """Role response with permissions (detail view)."""

    permissions: list[PermissionResponse]
