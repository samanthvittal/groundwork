"""Tests for auth dependencies."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_get_current_user_returns_user_from_valid_token() -> None:
    """get_current_user should return user when token is valid."""
    from uuid import uuid4

    from groundwork.auth.dependencies import get_current_user

    user_id = uuid4()
    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.is_active = True

    mock_request = MagicMock()
    mock_request.cookies = {"access_token": "valid.token.here"}

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute.return_value = mock_result

    with patch("groundwork.auth.dependencies.decode_token") as mock_decode:
        mock_decode.return_value = {"sub": str(user_id), "type": "access"}
        result = await get_current_user(mock_request, mock_db)

    assert result is mock_user


@pytest.mark.asyncio
async def test_get_current_user_raises_401_for_missing_token() -> None:
    """get_current_user should raise 401 when no token provided."""
    from groundwork.auth.dependencies import get_current_user

    mock_request = MagicMock()
    mock_request.cookies = {}

    mock_db = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(mock_request, mock_db)

    assert exc_info.value.status_code == 401


def test_require_permission_raises_403_when_permission_missing() -> None:
    """require_permission should raise 403 when user lacks permission."""
    from groundwork.auth.dependencies import require_permission

    mock_user = MagicMock()
    mock_user.role.has_permission.return_value = False

    checker = require_permission("users:create")

    with pytest.raises(HTTPException) as exc_info:
        checker(mock_user)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_current_user_raises_401_for_invalid_token() -> None:
    """get_current_user should raise 401 when token is invalid."""
    from groundwork.auth.dependencies import get_current_user

    mock_request = MagicMock()
    mock_request.cookies = {"access_token": "invalid.token.here"}

    mock_db = AsyncMock()

    with patch("groundwork.auth.dependencies.decode_token") as mock_decode:
        mock_decode.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_db)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_raises_401_for_refresh_token() -> None:
    """get_current_user should raise 401 when token type is not 'access'."""
    from uuid import uuid4

    from groundwork.auth.dependencies import get_current_user

    mock_request = MagicMock()
    mock_request.cookies = {"access_token": "valid.but.refresh"}

    mock_db = AsyncMock()

    with patch("groundwork.auth.dependencies.decode_token") as mock_decode:
        mock_decode.return_value = {"sub": str(uuid4()), "type": "refresh"}
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_db)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_raises_401_for_invalid_uuid() -> None:
    """get_current_user should raise 401 when sub is not a valid UUID."""
    from groundwork.auth.dependencies import get_current_user

    mock_request = MagicMock()
    mock_request.cookies = {"access_token": "valid.token"}

    mock_db = AsyncMock()

    with patch("groundwork.auth.dependencies.decode_token") as mock_decode:
        mock_decode.return_value = {"sub": "not-a-valid-uuid", "type": "access"}
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_db)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_raises_401_for_inactive_user() -> None:
    """get_current_user should raise 401 when user is inactive."""
    from uuid import uuid4

    from groundwork.auth.dependencies import get_current_user

    user_id = uuid4()
    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.is_active = False

    mock_request = MagicMock()
    mock_request.cookies = {"access_token": "valid.token"}

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute.return_value = mock_result

    with patch("groundwork.auth.dependencies.decode_token") as mock_decode:
        mock_decode.return_value = {"sub": str(user_id), "type": "access"}
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_db)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_raises_401_for_nonexistent_user() -> None:
    """get_current_user should raise 401 when user doesn't exist."""
    from uuid import uuid4

    from groundwork.auth.dependencies import get_current_user

    mock_request = MagicMock()
    mock_request.cookies = {"access_token": "valid.token"}

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with patch("groundwork.auth.dependencies.decode_token") as mock_decode:
        mock_decode.return_value = {"sub": str(uuid4()), "type": "access"}
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_db)

    assert exc_info.value.status_code == 401


def test_require_permission_returns_user_when_permission_exists() -> None:
    """require_permission should return user when they have the permission."""
    from groundwork.auth.dependencies import require_permission

    mock_user = MagicMock()
    mock_user.role.has_permission.return_value = True

    checker = require_permission("users:read")
    result = checker(mock_user)

    assert result is mock_user
