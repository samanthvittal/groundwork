"""Health check API routes."""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.core.database import get_db
from groundwork.health.schemas import HealthDetails, HealthStatus
from groundwork.health.services import HealthService

router = APIRouter()


@router.get("/live", response_model=HealthStatus)
async def liveness() -> HealthStatus:
    """Liveness probe - app is running."""
    return HealthStatus(status="ok")


@router.get("/ready", response_model=HealthStatus)
async def readiness(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> HealthStatus:
    """Readiness probe - app is ready to serve traffic."""
    service = HealthService(db)
    is_ready = await service.check_readiness()
    if not is_ready:
        response.status_code = 503
        return HealthStatus(status="unavailable")
    return HealthStatus(status="ok")


@router.get("/details", response_model=HealthDetails)
async def details(db: AsyncSession = Depends(get_db)) -> HealthDetails:
    """Detailed health information."""
    service = HealthService(db)
    details_dict = await service.get_details()
    return HealthDetails(**details_dict)
