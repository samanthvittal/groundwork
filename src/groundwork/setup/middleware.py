"""Setup check middleware for first-run detection."""

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.types import ASGIApp

from groundwork.setup.models import InstanceConfig

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


# Module-level session factory override for testing
_session_factory_override: "async_sessionmaker[AsyncSession] | None" = None

# Module-level reference to the middleware instance for cache reset
_middleware_instance: "SetupCheckMiddleware | None" = None


def set_session_factory_override(
    factory: "async_sessionmaker[AsyncSession] | None",
) -> None:
    """Set a session factory override for testing.

    Args:
        factory: The session factory to use, or None to use the default.
    """
    global _session_factory_override
    _session_factory_override = factory


def reset_setup_cache() -> None:
    """Reset the setup middleware's cached status.

    Call this after setup completion so the middleware re-checks the database.
    """
    if _middleware_instance is not None:
        _middleware_instance.reset_cache()


def _get_session_factory() -> "async_sessionmaker[AsyncSession]":
    """Get the session factory, using override if set.

    Returns:
        The session factory to use.
    """
    if _session_factory_override is not None:
        return _session_factory_override
    # Import here to avoid circular imports and allow override
    from groundwork.core.database import get_session_factory

    return get_session_factory()


class SetupCheckMiddleware(BaseHTTPMiddleware):
    """Middleware to redirect to setup wizard if setup is not complete."""

    # Paths that should bypass the setup check
    BYPASS_PREFIXES = (
        "/setup",
        "/health",
        "/api/v1/health",
        "/api/v1/setup",
        "/static",
    )

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the middleware.

        Args:
            app: The ASGI application instance.
        """
        super().__init__(app)
        self._setup_completed: bool | None = None  # Cache status

        # Store reference for reset_setup_cache()
        global _middleware_instance
        _middleware_instance = self

    def reset_cache(self) -> None:
        """Reset the cached setup status.

        This is useful for testing and when setup state changes.
        """
        self._setup_completed = None

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Check setup status and redirect if setup is not complete.

        Args:
            request: The incoming request.
            call_next: The next middleware or route handler.

        Returns:
            The response, either a redirect or the normal response.
        """
        # Check paths that should bypass the setup check
        path = request.url.path
        if any(path.startswith(prefix) for prefix in self.BYPASS_PREFIXES):
            return await call_next(request)

        # Check setup status (with caching)
        if self._setup_completed is None:
            self._setup_completed = await self._check_setup_status()

        if not self._setup_completed:
            return RedirectResponse(url="/setup", status_code=307)

        return await call_next(request)

    async def _check_setup_status(self) -> bool:
        """Check if setup has been completed by querying the database.

        Returns:
            True if setup is complete, False otherwise.
        """
        session_factory = _get_session_factory()
        async with session_factory() as session:
            result = await session.execute(
                select(InstanceConfig.setup_completed).limit(1)
            )
            row = result.scalar_one_or_none()
            return row is True
