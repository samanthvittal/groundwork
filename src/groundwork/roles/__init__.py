"""Role management module."""

from groundwork.roles.routes import router
from groundwork.roles.services import RoleService

__all__ = ["router", "RoleService"]
