"""Health check services."""

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.core.config import get_settings


class HealthService:
    """Service for performing health checks."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize health service with database session."""
        self.db = db
        self.settings = get_settings()

    async def check_readiness(self) -> bool:
        """Check if application is ready to serve traffic."""
        try:
            await self.db.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def get_details(self) -> dict[str, Any]:
        """Get detailed health information."""
        db_ok = await self.check_readiness()
        return {
            "status": "ok" if db_ok else "degraded",
            "version": "0.1.0",
            "environment": self.settings.environment,
            "components": {
                "database": {"status": "ok" if db_ok else "unavailable"},
            },
        }
