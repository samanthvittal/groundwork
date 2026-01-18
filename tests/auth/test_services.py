"""Tests for auth service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_auth_service_login_returns_tokens() -> None:
    """AuthService.login should return access and refresh tokens."""
    from groundwork.auth.services import AuthService

    mock_db = AsyncMock()
    mock_user = MagicMock()
    mock_user.id = "user-id-123"

    with patch("groundwork.auth.services.LocalAuthProvider") as mock_provider_class:
        mock_provider = AsyncMock()
        mock_provider.authenticate.return_value = mock_user
        mock_provider_class.return_value = mock_provider

        service = AuthService(mock_db)
        result = await service.login("test@example.com", "password123")

    assert result is not None
    assert "access_token" in result
    assert "refresh_token" in result
    assert result["user"] is mock_user


@pytest.mark.asyncio
async def test_auth_service_login_returns_none_for_invalid_credentials() -> None:
    """AuthService.login should return None for invalid credentials."""
    from groundwork.auth.services import AuthService

    mock_db = AsyncMock()

    with patch("groundwork.auth.services.LocalAuthProvider") as mock_provider_class:
        mock_provider = AsyncMock()
        mock_provider.authenticate.return_value = None
        mock_provider_class.return_value = mock_provider

        service = AuthService(mock_db)
        result = await service.login("test@example.com", "wrongpassword")

    assert result is None
