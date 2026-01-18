"""Tests for auth providers."""

from abc import ABC

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
