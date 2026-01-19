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


@pytest.mark.asyncio
async def test_instance_config_with_smtp(db_session) -> None:
    """InstanceConfig should store SMTP configuration."""
    from groundwork.setup.models import InstanceConfig

    config = InstanceConfig(
        instance_name="Test Instance",
        base_url="http://localhost:8000",
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="smtp_user",
        smtp_password="smtp_pass",
        smtp_from_address="noreply@example.com",
        smtp_configured=True,
    )
    db_session.add(config)
    await db_session.commit()

    assert config.smtp_host == "smtp.example.com"
    assert config.smtp_port == 587
    assert config.smtp_username == "smtp_user"
    assert config.smtp_password == "smtp_pass"
    assert config.smtp_from_address == "noreply@example.com"
    assert config.smtp_configured is True


@pytest.mark.asyncio
async def test_instance_config_full_configuration(db_session) -> None:
    """InstanceConfig should store full configuration with all fields."""
    from groundwork.setup.models import InstanceConfig

    config = InstanceConfig(
        instance_name="Production Instance",
        base_url="https://app.example.com",
        setup_completed=True,
        smtp_host="mail.example.com",
        smtp_port=465,
        smtp_username="mail_user",
        smtp_password="secure_password",
        smtp_from_address="admin@example.com",
        smtp_configured=True,
    )
    db_session.add(config)
    await db_session.commit()

    # Verify all fields are correctly stored
    assert config.instance_name == "Production Instance"
    assert config.base_url == "https://app.example.com"
    assert config.setup_completed is True
    assert config.smtp_host == "mail.example.com"
    assert config.smtp_port == 465
    assert config.smtp_username == "mail_user"
    assert config.smtp_password == "secure_password"
    assert config.smtp_from_address == "admin@example.com"
    assert config.smtp_configured is True
    assert config.created_at is not None
    assert config.updated_at is not None
