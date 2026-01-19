"""User management Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# Request schemas
class UserCreate(BaseModel):
    """Create user request."""

    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role_id: UUID
    display_name: str | None = Field(default=None, max_length=200)
    timezone: str = Field(default="UTC", max_length=50)
    language: str = Field(default="en", max_length=10)
    theme: str = Field(default="system", max_length=20)


class UserUpdate(BaseModel):
    """Update user request - all fields optional."""

    email: EmailStr | None = None
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    role_id: UUID | None = None
    display_name: str | None = Field(default=None, max_length=200)
    timezone: str | None = Field(default=None, max_length=50)
    language: str | None = Field(default=None, max_length=10)
    theme: str | None = Field(default=None, max_length=20)
    is_active: bool | None = None
    email_verified: bool | None = None


class PasswordReset(BaseModel):
    """Admin password reset request."""

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
    role_id: UUID
    timezone: str
    language: str
    theme: str
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None

    model_config = {"from_attributes": True}


class UserDetailResponse(UserResponse):
    """User response with role details."""

    # Extend as needed when role details are required
    pass
