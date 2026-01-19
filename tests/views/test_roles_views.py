"""Tests for role management views."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_roles_list_returns_response(client: AsyncClient) -> None:
    """GET /roles should return response or redirect."""
    response = await client.get("/roles", follow_redirects=False)
    # Should return 401 Unauthorized when not logged in,
    # or 307 redirect if setup is not complete
    assert response.status_code in [307, 401]
