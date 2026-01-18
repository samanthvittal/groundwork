"""Tests for setup models."""

import pytest


@pytest.mark.asyncio
async def test_instance_config_created(db_session) -> None:
    """InstanceConfig should store instance settings."""
    from groundwork.setup.models import InstanceConfig

    config = InstanceConfig(
        instance_name="Test Instance",
        base_url="http://localhost:8000",
    )
    db_session.add(config)
    await db_session.commit()

    assert config.setup_completed is False
    assert config.smtp_configured is False
