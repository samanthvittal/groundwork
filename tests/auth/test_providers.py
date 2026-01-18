"""Tests for auth providers."""

from abc import ABC

import pytest


def test_auth_provider_is_abstract() -> None:
    """AuthProvider should be an abstract base class."""
    from groundwork.auth.providers.base import AuthProvider

    assert issubclass(AuthProvider, ABC)

    with pytest.raises(TypeError):
        AuthProvider()  # Cannot instantiate abstract class
