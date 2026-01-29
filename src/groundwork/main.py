"""FastAPI application factory."""

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from groundwork.core.config import get_settings
from groundwork.core.database import get_engine, get_session_factory
from groundwork.core.logging import get_logger, setup_logging
from groundwork.core.seed import seed_defaults
from groundwork.health.routes import router as health_router
from groundwork.issues.routes import router as issues_router
from groundwork.profile.routes import router as profile_router
from groundwork.projects.routes import router as projects_router
from groundwork.roles.routes import router as roles_router
from groundwork.setup.middleware import SetupCheckMiddleware
from groundwork.setup.routes import router as setup_router
from groundwork.users.routes import router as users_router
from groundwork.views import (
    auth_router as auth_view_router,
)
from groundwork.views import (
    issues_router as issues_view_router,
)
from groundwork.views import (
    profile_router as profile_view_router,
)
from groundwork.views import (
    projects_router as projects_view_router,
)
from groundwork.views import (
    roles_router as roles_view_router,
)
from groundwork.views import (
    setup_router as setup_view_router,
)
from groundwork.views import (
    users_router as users_view_router,
)
from groundwork.views.placeholder import router as placeholder_view_router

logger = get_logger(__name__)

# Path configuration for static files
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan - startup and shutdown events."""
    settings = get_settings()
    logger.info(
        "Starting Groundwork",
        extra={"version": app.version, "environment": settings.environment},
    )

    # Seed default roles and permissions
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            await seed_defaults(session)
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to seed defaults: {e}")
            raise

    yield
    engine = get_engine()
    await engine.dispose()
    logger.info("Shutting down Groundwork")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup check middleware - redirect to setup wizard if setup not complete
    app.add_middleware(SetupCheckMiddleware)

    # Request ID middleware
    @app.middleware("http")
    async def request_id_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Mount static files
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Add template context processor for common variables
    @app.middleware("http")
    async def template_context_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Make common template variables available via request.state
        request.state.current_year = datetime.now().year
        request.state.app_version = app.version
        request.state.instance_name = settings.app_name
        return await call_next(request)

    # Include routers
    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(setup_router, prefix="/api/v1/setup", tags=["setup"])
    app.include_router(profile_router, prefix="/api/v1/profile", tags=["profile"])
    app.include_router(projects_router, prefix="/api/v1/projects", tags=["projects"])
    app.include_router(issues_router, prefix="/api/v1", tags=["issues"])
    app.include_router(roles_router, prefix="/api/v1/roles", tags=["roles"])
    app.include_router(users_router, prefix="/api/v1/users", tags=["users"])

    # View routes (HTML pages)
    app.include_router(setup_view_router, tags=["setup-views"])
    app.include_router(auth_view_router, tags=["auth-views"])
    app.include_router(profile_view_router, tags=["profile-views"])
    app.include_router(projects_view_router, tags=["projects-views"])
    app.include_router(issues_view_router, tags=["issues-views"])
    app.include_router(users_view_router, tags=["users-views"])
    app.include_router(roles_view_router, tags=["roles-views"])
    app.include_router(placeholder_view_router, tags=["placeholder-views"])

    # Root redirect - goes to users page (requires auth, so will redirect to login if needed)
    @app.get("/")
    async def root() -> RedirectResponse:
        """Redirect root to users page."""
        return RedirectResponse(url="/users", status_code=303)

    # Exception handler for 401 errors - redirect to login for non-API routes
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> Response:
        """Handle HTTP exceptions - redirect 401 to login for view routes."""
        from fastapi.responses import JSONResponse

        # For 401 errors on non-API routes, redirect to login
        if exc.status_code == 401 and not request.url.path.startswith("/api/"):
            return RedirectResponse(url="/login", status_code=303)

        # For API routes or other errors, return JSON response
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    return app


# Application instance for uvicorn
app = create_app()
