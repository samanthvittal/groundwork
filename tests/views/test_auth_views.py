"""Tests for auth views."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_page_returns_response(client: AsyncClient) -> None:
    """GET /login should return login page HTML or redirect."""
    response = await client.get("/login", follow_redirects=False)
    # Should either return 200 with HTML, 303 redirect if logged in,
    # or 307 redirect if setup not complete
    assert response.status_code in [200, 303, 307]
