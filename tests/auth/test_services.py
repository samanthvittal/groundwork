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


@pytest.mark.asyncio
async def test_request_password_reset_returns_token_for_existing_user() -> None:
    """AuthService.request_password_reset should return token for existing user."""
    from groundwork.auth.services import AuthService

    user_id = uuid4()
    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.email = "test@example.com"
    mock_user.is_active = True

    mock_user_result = MagicMock()
    mock_user_result.scalar_one_or_none.return_value = mock_user

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_user_result

    with patch("groundwork.auth.services.LocalAuthProvider"):
        service = AuthService(mock_db)
        result = await service.request_password_reset("test@example.com")

    assert result is not None
    assert isinstance(result, str)
    # Token format should be selector.validator
    assert "." in result
    parts = result.split(".", 1)
    assert len(parts) == 2
    assert len(parts[0]) == 16  # selector is 16 chars
    assert len(parts[1]) > 0  # validator has content
    mock_db.add.assert_called_once()
    mock_db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_request_password_reset_returns_none_for_nonexistent_user() -> None:
    """AuthService.request_password_reset should return None for nonexistent user."""
    from groundwork.auth.services import AuthService

    mock_user_result = MagicMock()
    mock_user_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_user_result

    with patch("groundwork.auth.services.LocalAuthProvider"):
        service = AuthService(mock_db)
        result = await service.request_password_reset("nonexistent@example.com")

    assert result is None
    mock_db.add.assert_not_called()


@pytest.mark.asyncio
async def test_request_password_reset_returns_none_for_inactive_user() -> None:
    """AuthService.request_password_reset should return None for inactive user."""
    from groundwork.auth.services import AuthService

    mock_user = MagicMock()
    mock_user.id = uuid4()
    mock_user.email = "test@example.com"
    mock_user.is_active = False

    mock_user_result = MagicMock()
    mock_user_result.scalar_one_or_none.return_value = mock_user

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_user_result

    with patch("groundwork.auth.services.LocalAuthProvider"):
        service = AuthService(mock_db)
        result = await service.request_password_reset("test@example.com")

    assert result is None
    mock_db.add.assert_not_called()


@pytest.mark.asyncio
async def test_confirm_password_reset_success() -> None:
    """AuthService.confirm_password_reset should reset password with valid token."""
    from groundwork.auth.services import AuthService
    from groundwork.auth.utils import hash_password

    user_id = uuid4()
    # Token format: selector.validator
    selector = "test-selector-1234"
    validator = "test-validator-secret"
    full_token = f"{selector}.{validator}"
    validator_hash = hash_password(validator)

    mock_reset_token = MagicMock()
    mock_reset_token.token_selector = selector
    mock_reset_token.token_hash = validator_hash
    mock_reset_token.user_id = user_id
    mock_reset_token.used_at = None
    mock_reset_token.expires_at = datetime.now(UTC) + timedelta(hours=1)

    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.hashed_password = "old-hash"

    mock_refresh_token = MagicMock()
    mock_refresh_token.revoked_at = None

    # Set up mock db responses - O(1) lookup by selector
    mock_token_result = MagicMock()
    mock_token_result.scalar_one_or_none.return_value = mock_reset_token

    mock_user_result = MagicMock()
    mock_user_result.scalar_one_or_none.return_value = mock_user

    mock_refresh_result = MagicMock()
    mock_refresh_result.scalars.return_value = [mock_refresh_token]

    mock_db = AsyncMock()
    mock_db.execute.side_effect = [
        mock_token_result,
        mock_user_result,
        mock_refresh_result,
    ]

    with patch("groundwork.auth.services.LocalAuthProvider"):
        service = AuthService(mock_db)
        result = await service.confirm_password_reset(full_token, "newpassword123")

    assert result is True
    assert mock_reset_token.used_at is not None
    assert mock_user.hashed_password != "old-hash"
    assert mock_refresh_token.revoked_at is not None
    mock_db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_confirm_password_reset_invalid_format_no_dot() -> None:
    """AuthService.confirm_password_reset should return False for token without dot."""
    from groundwork.auth.services import AuthService

    mock_db = AsyncMock()

    with patch("groundwork.auth.services.LocalAuthProvider"):
        service = AuthService(mock_db)
        result = await service.confirm_password_reset(
            "invalid-token-no-dot", "newpassword123"
        )

    assert result is False
    # No database call should be made for invalid format
    mock_db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_confirm_password_reset_selector_not_found() -> None:
    """AuthService.confirm_password_reset should return False when selector not found."""
    from groundwork.auth.services import AuthService

    # Token with valid format but selector doesn't exist
    mock_token_result = MagicMock()
    mock_token_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_token_result

    with patch("groundwork.auth.services.LocalAuthProvider"):
        service = AuthService(mock_db)
        result = await service.confirm_password_reset(
            "unknown-selector.some-validator", "newpassword123"
        )

    assert result is False


@pytest.mark.asyncio
async def test_confirm_password_reset_wrong_validator() -> None:
    """AuthService.confirm_password_reset should return False for wrong validator."""
    from groundwork.auth.services import AuthService
    from groundwork.auth.utils import hash_password

    user_id = uuid4()
    selector = "test-selector"
    correct_validator = "correct-validator"

    mock_reset_token = MagicMock()
    mock_reset_token.token_selector = selector
    mock_reset_token.token_hash = hash_password(correct_validator)
    mock_reset_token.user_id = user_id
    mock_reset_token.used_at = None
    mock_reset_token.expires_at = datetime.now(UTC) + timedelta(hours=1)

    mock_token_result = MagicMock()
    mock_token_result.scalar_one_or_none.return_value = mock_reset_token

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_token_result

    with patch("groundwork.auth.services.LocalAuthProvider"):
        service = AuthService(mock_db)
        # Use wrong validator
        result = await service.confirm_password_reset(
            f"{selector}.wrong-validator", "newpassword123"
        )

    assert result is False


@pytest.mark.asyncio
async def test_confirm_password_reset_expired_token() -> None:
    """AuthService.confirm_password_reset should return False for expired token."""
    from groundwork.auth.services import AuthService

    # Token exists but is expired (query should not return it due to expiry filter)
    mock_token_result = MagicMock()
    mock_token_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_token_result

    with patch("groundwork.auth.services.LocalAuthProvider"):
        service = AuthService(mock_db)
        result = await service.confirm_password_reset(
            "selector.expired-validator", "newpassword123"
        )

    assert result is False


@pytest.mark.asyncio
async def test_confirm_password_reset_revokes_all_refresh_tokens() -> None:
    """AuthService.confirm_password_reset should revoke all user's refresh tokens."""
    from groundwork.auth.services import AuthService
    from groundwork.auth.utils import hash_password

    user_id = uuid4()
    # Token format: selector.validator
    selector = "revoke-selector"
    validator = "revoke-validator"
    full_token = f"{selector}.{validator}"
    validator_hash = hash_password(validator)

    mock_reset_token = MagicMock()
    mock_reset_token.token_selector = selector
    mock_reset_token.token_hash = validator_hash
    mock_reset_token.user_id = user_id
    mock_reset_token.used_at = None
    mock_reset_token.expires_at = datetime.now(UTC) + timedelta(hours=1)

    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.hashed_password = "old-hash"

    # Multiple refresh tokens
    mock_refresh_token1 = MagicMock()
    mock_refresh_token1.revoked_at = None
    mock_refresh_token2 = MagicMock()
    mock_refresh_token2.revoked_at = None

    # O(1) lookup by selector
    mock_token_result = MagicMock()
    mock_token_result.scalar_one_or_none.return_value = mock_reset_token

    mock_user_result = MagicMock()
    mock_user_result.scalar_one_or_none.return_value = mock_user

    mock_refresh_result = MagicMock()
    mock_refresh_result.scalars.return_value = [
        mock_refresh_token1,
        mock_refresh_token2,
    ]

    mock_db = AsyncMock()
    mock_db.execute.side_effect = [
        mock_token_result,
        mock_user_result,
        mock_refresh_result,
    ]

    with patch("groundwork.auth.services.LocalAuthProvider"):
        service = AuthService(mock_db)
        result = await service.confirm_password_reset(full_token, "newpassword123")

    assert result is True
    assert mock_refresh_token1.revoked_at is not None
    assert mock_refresh_token2.revoked_at is not None
