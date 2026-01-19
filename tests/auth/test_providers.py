"""Tests for auth providers."""

from abc import ABC
from unittest.mock import AsyncMock, MagicMock

import pytest


def test_auth_provider_is_abstract() -> None:
    """AuthProvider should be an abstract base class."""
    from groundwork.auth.providers.base import AuthProvider

    assert issubclass(AuthProvider, ABC)

    with pytest.raises(TypeError):
        AuthProvider()  # Cannot instantiate abstract class


def test_auth_provider_has_required_methods() -> None:
    """AuthProvider should define all required authentication methods."""
    from groundwork.auth.providers.base import AuthProvider

    abstract_methods = AuthProvider.__abstractmethods__
    expected = {"authenticate", "create_user", "change_password", "verify_email"}
    assert abstract_methods == expected


def test_concrete_provider_must_implement_all_methods() -> None:
    """A concrete provider missing methods should fail to instantiate."""
    from groundwork.auth.providers.base import AuthProvider

    class IncompleteProvider(AuthProvider):
        async def authenticate(self, email: str, password: str):
            pass

    with pytest.raises(TypeError):
        IncompleteProvider()


@pytest.mark.asyncio
async def test_local_auth_provider_authenticate_returns_user() -> None:
    """LocalAuthProvider.authenticate should return user for valid credentials."""
    from groundwork.auth.providers.local import LocalAuthProvider
    from groundwork.auth.utils import hash_password

    mock_session = AsyncMock()
    provider = LocalAuthProvider(mock_session)

    # Create a mock user
    mock_user = MagicMock()
    mock_user.hashed_password = hash_password("correctpassword")
    mock_user.is_active = True

    # Mock the query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result

    result = await provider.authenticate("test@example.com", "correctpassword")

    assert result is mock_user


@pytest.mark.asyncio
async def test_local_auth_provider_authenticate_returns_none_for_wrong_password() -> (
    None
):
    """LocalAuthProvider.authenticate should return None for wrong password."""
    from groundwork.auth.providers.local import LocalAuthProvider
    from groundwork.auth.utils import hash_password

    mock_session = AsyncMock()
    provider = LocalAuthProvider(mock_session)

    mock_user = MagicMock()
    mock_user.hashed_password = hash_password("correctpassword")
    mock_user.is_active = True

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result

    result = await provider.authenticate("test@example.com", "wrongpassword")

    assert result is None


@pytest.mark.asyncio
async def test_local_auth_provider_authenticate_returns_none_for_nonexistent_user() -> (
    None
):
    """LocalAuthProvider.authenticate should return None for nonexistent user."""
    from groundwork.auth.providers.local import LocalAuthProvider

    mock_session = AsyncMock()
    provider = LocalAuthProvider(mock_session)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await provider.authenticate("nonexistent@example.com", "anypassword")

    assert result is None


@pytest.mark.asyncio
async def test_local_auth_provider_authenticate_returns_none_for_inactive_user() -> (
    None
):
    """LocalAuthProvider.authenticate should return None for inactive user."""
    from groundwork.auth.providers.local import LocalAuthProvider
    from groundwork.auth.utils import hash_password

    mock_session = AsyncMock()
    provider = LocalAuthProvider(mock_session)

    mock_user = MagicMock()
    mock_user.hashed_password = hash_password("correctpassword")
    mock_user.is_active = False  # Inactive user

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result

    result = await provider.authenticate("test@example.com", "correctpassword")

    assert result is None


@pytest.mark.asyncio
async def test_local_auth_provider_create_user() -> None:
    """LocalAuthProvider.create_user should create user with hashed password."""
    from uuid import uuid4

    from groundwork.auth.providers.local import LocalAuthProvider

    mock_session = AsyncMock()
    provider = LocalAuthProvider(mock_session)

    role_id = uuid4()
    user = await provider.create_user(
        email="new@example.com",
        password="password123",
        first_name="New",
        last_name="User",
        role_id=role_id,
    )

    assert user.email == "new@example.com"
    assert user.first_name == "New"
    assert user.last_name == "User"
    assert user.hashed_password != "password123"
    assert user.hashed_password.startswith("$argon2")
    mock_session.add.assert_called_once_with(user)
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_local_auth_provider_change_password() -> None:
    """LocalAuthProvider.change_password should update hashed password."""
    from groundwork.auth.providers.local import LocalAuthProvider
    from groundwork.auth.utils import hash_password, verify_password

    mock_session = AsyncMock()
    provider = LocalAuthProvider(mock_session)

    mock_user = MagicMock()
    mock_user.hashed_password = hash_password("oldpassword")

    await provider.change_password(mock_user, "newpassword")

    assert mock_user.hashed_password.startswith("$argon2")
    assert verify_password("newpassword", mock_user.hashed_password) is True
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_local_auth_provider_verify_email() -> None:
    """LocalAuthProvider.verify_email should set email_verified to True."""
    from groundwork.auth.providers.local import LocalAuthProvider

    mock_session = AsyncMock()
    provider = LocalAuthProvider(mock_session)

    mock_user = MagicMock()
    mock_user.email_verified = False

    await provider.verify_email(mock_user)

    assert mock_user.email_verified is True
    mock_session.flush.assert_called_once()
