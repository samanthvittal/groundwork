"""Profile management Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# Request schemas
class ProfileUpdate(BaseModel):
    """Update profile request - all fields optional."""

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    display_name: str | None = Field(default=None, max_length=200)


class PasswordChange(BaseModel):
    """Change password request."""

    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


class SettingsUpdate(BaseModel):
    """Update user preferences request - all fields optional."""

    timezone: str | None = Field(default=None, max_length=50)
    language: str | None = Field(default=None, max_length=10)
    theme: str | None = Field(default=None, max_length=20)


# Response schemas
class ProfileResponse(BaseModel):
    """User profile response model."""

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


class SettingsResponse(BaseModel):
    """User settings/preferences response model."""

    timezone: str
    language: str
    theme: str

    model_config = {"from_attributes": True}


class AvatarResponse(BaseModel):
    """Avatar upload response model."""

    avatar_path: str
