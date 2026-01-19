"""Setup wizard Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, HttpUrl

# =============================================================================
# Request schemas
# =============================================================================


class InstanceSettingsRequest(BaseModel):
    """Request body for saving instance settings."""

    instance_name: str = Field(min_length=1, max_length=200)
    base_url: HttpUrl


class AdminCreateRequest(BaseModel):
    """Request body for creating admin user."""

    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    password: str


class SmtpConfigRequest(BaseModel):
    """Request body for SMTP configuration."""

    smtp_host: str = Field(min_length=1, max_length=255)
    smtp_port: int = Field(ge=1, le=65535)
    smtp_username: str | None = Field(default=None, max_length=255)
    smtp_password: str | None = Field(default=None, max_length=255)
    smtp_from_address: EmailStr


# =============================================================================
# Response schemas
# =============================================================================


class SetupStatusResponse(BaseModel):
    """Response for setup status endpoint."""

    setup_completed: bool
    current_step: str | None


class InstanceConfigResponse(BaseModel):
    """Response for instance configuration.

    Note: smtp_password is intentionally excluded from this response schema
    to prevent exposing sensitive credentials in API responses.
    """

    id: UUID
    instance_name: str
    base_url: str
    setup_completed: bool
    smtp_host: str | None
    smtp_port: int | None
    smtp_username: str | None
    # smtp_password is intentionally excluded - never expose passwords in API responses
    smtp_from_address: str | None
    smtp_configured: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdminUserResponse(BaseModel):
    """Response for created admin user."""

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


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str
