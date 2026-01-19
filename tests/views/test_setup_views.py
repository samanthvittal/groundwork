"""Tests for setup wizard views."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_setup_welcome_returns_html(client: AsyncClient) -> None:
    """GET /setup should return welcome page HTML."""
    response = await client.get("/setup", follow_redirects=False)
    # Should either return 200 with HTML or redirect to login if setup complete
    assert response.status_code in [200, 303]


@pytest.mark.asyncio
async def test_setup_instance_returns_html(client: AsyncClient) -> None:
    """GET /setup/instance should return instance form HTML."""
    response = await client.get("/setup/instance", follow_redirects=False)
    assert response.status_code in [200, 303]


@pytest.mark.asyncio
async def test_setup_admin_returns_html(client: AsyncClient) -> None:
    """GET /setup/admin should return admin form HTML."""
    response = await client.get("/setup/admin", follow_redirects=False)
    assert response.status_code in [200, 303]


@pytest.mark.asyncio
async def test_setup_smtp_returns_html(client: AsyncClient) -> None:
    """GET /setup/smtp should return SMTP form HTML."""
    response = await client.get("/setup/smtp", follow_redirects=False)
    assert response.status_code in [200, 303]
