"""FastAPI application factory."""

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from groundwork.core.config import get_settings
from groundwork.core.database import get_engine
from groundwork.core.logging import get_logger, setup_logging
from groundwork.health.routes import router as health_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan - startup and shutdown events."""
    settings = get_settings()
    logger.info(
        "Starting Groundwork",
        extra={"version": app.version, "environment": settings.environment},
    )
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

    # Include routers
    app.include_router(health_router, prefix="/health", tags=["health"])

    return app


# Application instance for uvicorn
app = create_app()
