"""View routes for HTML pages."""

from groundwork.views.auth import router as auth_router
from groundwork.views.profile import router as profile_router
from groundwork.views.projects import router as projects_router
from groundwork.views.roles import router as roles_router
from groundwork.views.setup import router as setup_router
from groundwork.views.users import router as users_router

__all__ = [
    "auth_router",
    "profile_router",
    "projects_router",
    "roles_router",
    "setup_router",
    "users_router",
]
