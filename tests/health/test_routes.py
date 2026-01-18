"""Tests for health routes."""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_liveness_returns_ok() -> None:
    """GET /health/live should return status ok."""
    from groundwork.health.routes import router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router, prefix="/health")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
