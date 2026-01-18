"""Health check schemas."""

from pydantic import BaseModel


class HealthStatus(BaseModel):
    """Basic health status response."""

    status: str


class ComponentStatus(BaseModel):
    """Individual component status."""

    status: str


class HealthDetails(BaseModel):
    """Detailed health response."""

    status: str
    version: str
    environment: str
    components: dict[str, ComponentStatus]
