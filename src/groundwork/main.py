"""FastAPI application factory."""

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from groundwork.core.config import get_settings
from groundwork.core.database import get_engine, get_session_factory
from groundwork.core.logging import get_logger, setup_logging
from groundwork.core.seed import seed_defaults
from groundwork.health.routes import router as health_router
from groundwork.profile.routes import router as profile_router
from groundwork.roles.routes import router as roles_router
from groundwork.setup.middleware import SetupCheckMiddleware
from groundwork.setup.routes import router as setup_router
from groundwork.users.routes import router as users_router

logger = get_logger(__name__)

# Path configuration for templates and static files
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Initialize Jinja2Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def get_templates() -> Jinja2Templates:
    """Get the configured Jinja2Templates instance."""
    return templates


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
    app.include_router(roles_router, prefix="/api/v1/roles", tags=["roles"])
    app.include_router(users_router, prefix="/api/v1/users", tags=["users"])

    return app


# Application instance for uvicorn
app = create_app()
