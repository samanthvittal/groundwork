"""Database configuration and session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from groundwork.core.config import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


def _create_engine() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Create database engine and session factory."""
    settings = get_settings()

    engine = create_async_engine(
        str(settings.database_url),
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        echo=settings.debug,
    )

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    return engine, session_factory


# Lazy initialization - created on first use
_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get the database engine, creating it if needed."""
    global _engine, _async_session_factory
    if _engine is None:
        _engine, _async_session_factory = _create_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get the session factory, creating it if needed."""
    global _engine, _async_session_factory
    if _async_session_factory is None:
        _engine, _async_session_factory = _create_engine()
    return _async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI routes to get database session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
