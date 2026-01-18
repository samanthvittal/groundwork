"""Tests for configuration module."""

import pytest


def test_settings_loads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings should load values from environment variables."""
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test"
    )
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DEBUG", "false")

    # Clear the cache to force reload
    from groundwork.core.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()

    assert (
        str(settings.database_url)
        == "postgresql+asyncpg://test:test@localhost:5432/test"
    )
    assert settings.secret_key == "test-secret"
    assert settings.environment == "testing"
    assert settings.debug is False


def test_settings_has_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings should have sensible defaults."""
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test"
    )
    monkeypatch.setenv("SECRET_KEY", "test-secret")

    from groundwork.core.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.app_name == "Groundwork"
    assert settings.db_pool_size == 5
    assert settings.access_token_expire_minutes == 30


def test_settings_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_settings should return cached instance."""
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test"
    )
    monkeypatch.setenv("SECRET_KEY", "test-secret")

    from groundwork.core.config import get_settings

    get_settings.cache_clear()
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2
