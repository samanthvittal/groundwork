"""Tests for health services."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_settings() -> MagicMock:
    """Create mock settings for tests."""
    settings = MagicMock()
    settings.environment = "testing"
    return settings


@pytest.mark.asyncio
async def test_check_readiness_returns_true_when_db_connected(
    mock_settings: MagicMock,
) -> None:
    """check_readiness should return True when database is accessible."""
    with patch("groundwork.health.services.get_settings", return_value=mock_settings):
        from groundwork.health.services import HealthService

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=MagicMock())

        service = HealthService(mock_session)
        result = await service.check_readiness()

        assert result is True
        mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_check_readiness_returns_false_on_db_error(
    mock_settings: MagicMock,
) -> None:
    """check_readiness should return False when database is not accessible."""
    with patch("groundwork.health.services.get_settings", return_value=mock_settings):
        from groundwork.health.services import HealthService

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Connection failed"))

        service = HealthService(mock_session)
        result = await service.check_readiness()

        assert result is False


@pytest.mark.asyncio
async def test_get_details_returns_status_info(mock_settings: MagicMock) -> None:
    """get_details should return status and component info."""
    with patch("groundwork.health.services.get_settings", return_value=mock_settings):
        from groundwork.health.services import HealthService

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=MagicMock())

        service = HealthService(mock_session)
        result = await service.get_details()

        assert "status" in result
        assert "version" in result
        assert "environment" in result
        assert "components" in result
        assert "database" in result["components"]
