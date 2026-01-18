"""Tests for auth service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

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


@pytest.mark.asyncio
async def test_auth_service_logout_revokes_token() -> None:
    """AuthService.logout should revoke the specific refresh token."""
    from groundwork.auth.services import AuthService
    from groundwork.auth.utils import create_refresh_token, hash_password

    user_id = str(uuid4())
    refresh_token = create_refresh_token(user_id)
    token_hash = hash_password(refresh_token)

    mock_token = MagicMock()
    mock_token.token_hash = token_hash
    mock_token.revoked_at = None

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_token]

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    with patch("groundwork.auth.services.LocalAuthProvider"):
        service = AuthService(mock_db)
        result = await service.logout(refresh_token)

    assert result is True
    assert mock_token.revoked_at is not None


@pytest.mark.asyncio
async def test_auth_service_logout_returns_false_for_invalid_token() -> None:
    """AuthService.logout should return False for invalid token."""
    from groundwork.auth.services import AuthService

    mock_db = AsyncMock()

    with patch("groundwork.auth.services.LocalAuthProvider"):
        service = AuthService(mock_db)
        result = await service.logout("invalid-token")

    assert result is False


@pytest.mark.asyncio
async def test_auth_service_refresh_returns_tokens() -> None:
    """AuthService.refresh_access_token should return new tokens for valid refresh token."""
    from groundwork.auth.services import AuthService
    from groundwork.auth.utils import create_refresh_token, hash_password

    user_id = str(uuid4())
    refresh_token = create_refresh_token(user_id)
    token_hash = hash_password(refresh_token)

    mock_token = MagicMock()
    mock_token.token_hash = token_hash
    mock_token.revoked_at = None
    mock_token.expires_at = datetime.now(UTC) + timedelta(days=7)

    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.is_active = True

    # First call returns tokens, second call returns user
    mock_token_result = MagicMock()
    mock_token_result.scalars.return_value.all.return_value = [mock_token]

    mock_user_result = MagicMock()
    mock_user_result.scalar_one_or_none.return_value = mock_user

    mock_db = AsyncMock()
    mock_db.execute.side_effect = [mock_token_result, mock_user_result]

    with patch("groundwork.auth.services.LocalAuthProvider"):
        service = AuthService(mock_db)
        result = await service.refresh_access_token(refresh_token)

    assert result is not None
    assert "access_token" in result
    assert "csrf_token" in result
    assert result["user"] is mock_user


@pytest.mark.asyncio
async def test_auth_service_refresh_returns_none_for_invalid_token() -> None:
    """AuthService.refresh_access_token should return None for invalid token."""
    from groundwork.auth.services import AuthService

    mock_db = AsyncMock()

    with patch("groundwork.auth.services.LocalAuthProvider"):
        service = AuthService(mock_db)
        result = await service.refresh_access_token("invalid-token")

    assert result is None


@pytest.mark.asyncio
async def test_auth_service_refresh_returns_none_for_revoked_token() -> None:
    """AuthService.refresh_access_token should return None for revoked token."""
    from groundwork.auth.services import AuthService
    from groundwork.auth.utils import create_refresh_token

    user_id = str(uuid4())
    refresh_token = create_refresh_token(user_id)

    # Return empty list (no valid tokens found because they're all revoked)
    mock_token_result = MagicMock()
    mock_token_result.scalars.return_value.all.return_value = []

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_token_result

    with patch("groundwork.auth.services.LocalAuthProvider"):
        service = AuthService(mock_db)
        result = await service.refresh_access_token(refresh_token)

    assert result is None
