"""Authentication Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# Request schemas
class LoginRequest(BaseModel):
    """Login request body."""

    email: EmailStr
    password: str = Field(min_length=8)


class PasswordResetRequest(BaseModel):
    """Password reset request."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""

    token: str
    new_password: str = Field(min_length=8)


class ChangePasswordRequest(BaseModel):
    """Change password request."""

    current_password: str
    new_password: str = Field(min_length=8)


# Response schemas
class UserResponse(BaseModel):
    """User response model."""

    id: UUID
    email: str
    first_name: str
    last_name: str
    display_name: str | None
    avatar_path: str | None
    is_active: bool
    email_verified: bool
    timezone: str
    language: str
    theme: str
    created_at: datetime
    last_login_at: datetime | None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Token response for login."""

    user: UserResponse
    csrf_token: str


class RoleResponse(BaseModel):
    """Role response model."""

    id: UUID
    name: str
    description: str
    is_system: bool

    model_config = {"from_attributes": True}


class PermissionResponse(BaseModel):
    """Permission response model."""

    id: UUID
    codename: str
    description: str

    model_config = {"from_attributes": True}


class RoleDetailResponse(RoleResponse):
    """Role with permissions."""

    permissions: list[PermissionResponse]
