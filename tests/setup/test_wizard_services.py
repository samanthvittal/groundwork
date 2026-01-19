"""Tests for setup wizard services."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.models import Role, User
from groundwork.auth.utils import verify_password
from groundwork.setup.models import InstanceConfig

# =============================================================================
# SetupService.get_setup_status
# =============================================================================


@pytest.mark.asyncio
async def test_get_setup_status_no_config_returns_welcome(
    db_session: AsyncSession,
) -> None:
    """get_setup_status should return welcome step when no InstanceConfig exists."""
    from groundwork.setup.services import SetupService

    service = SetupService(db_session)
    status = await service.get_setup_status()

    assert status["setup_completed"] is False
    assert status["current_step"] == "welcome"


@pytest.mark.asyncio
async def test_get_setup_status_with_instance_returns_admin(
    db_session: AsyncSession,
) -> None:
    """get_setup_status should return admin step when instance configured but no admin."""
    from groundwork.setup.services import SetupService

    # Create instance config without admin
    config = InstanceConfig(
        instance_name="Test Instance",
        base_url="https://example.com",
        setup_completed=False,
    )
    db_session.add(config)
    await db_session.flush()

    service = SetupService(db_session)
    status = await service.get_setup_status()

    assert status["setup_completed"] is False
    assert status["current_step"] == "admin"


@pytest.mark.asyncio
async def test_get_setup_status_with_admin_returns_smtp(
    db_session: AsyncSession,
) -> None:
    """get_setup_status should return smtp step when admin exists but smtp not configured."""
    from groundwork.setup.services import SetupService

    # Create instance config
    config = InstanceConfig(
        instance_name="Test Instance",
        base_url="https://example.com",
        setup_completed=False,
        smtp_configured=False,
    )
    db_session.add(config)

    # Create Admin role with permissions
    admin_role = Role(
        name="Admin",
        description="Administrator",
        is_system=True,
    )
    db_session.add(admin_role)
    await db_session.flush()

    # Create admin user
    from groundwork.auth.utils import hash_password

    admin_user = User(
        email="admin@example.com",
        hashed_password=hash_password("password123"),
        first_name="Admin",
        last_name="User",
        role_id=admin_role.id,
    )
    db_session.add(admin_user)
    await db_session.flush()

    service = SetupService(db_session)
    status = await service.get_setup_status()

    assert status["setup_completed"] is False
    assert status["current_step"] == "smtp"


@pytest.mark.asyncio
async def test_get_setup_status_completed_returns_complete(
    db_session: AsyncSession,
) -> None:
    """get_setup_status should return complete step when setup is finished."""
    from groundwork.setup.services import SetupService

    config = InstanceConfig(
        instance_name="Test Instance",
        base_url="https://example.com",
        setup_completed=True,
    )
    db_session.add(config)
    await db_session.flush()

    service = SetupService(db_session)
    status = await service.get_setup_status()

    assert status["setup_completed"] is True
    assert status["current_step"] == "complete"


# =============================================================================
# SetupService.is_setup_complete
# =============================================================================


@pytest.mark.asyncio
async def test_is_setup_complete_false_when_no_config(
    db_session: AsyncSession,
) -> None:
    """is_setup_complete should return False when no InstanceConfig exists."""
    from groundwork.setup.services import SetupService

    service = SetupService(db_session)
    result = await service.is_setup_complete()

    assert result is False


@pytest.mark.asyncio
async def test_is_setup_complete_false_when_not_completed(
    db_session: AsyncSession,
) -> None:
    """is_setup_complete should return False when setup_completed is False."""
    from groundwork.setup.services import SetupService

    config = InstanceConfig(
        instance_name="Test Instance",
        base_url="https://example.com",
        setup_completed=False,
    )
    db_session.add(config)
    await db_session.flush()

    service = SetupService(db_session)
    result = await service.is_setup_complete()

    assert result is False


@pytest.mark.asyncio
async def test_is_setup_complete_true_when_completed(
    db_session: AsyncSession,
) -> None:
    """is_setup_complete should return True when setup_completed is True."""
    from groundwork.setup.services import SetupService

    config = InstanceConfig(
        instance_name="Test Instance",
        base_url="https://example.com",
        setup_completed=True,
    )
    db_session.add(config)
    await db_session.flush()

    service = SetupService(db_session)
    result = await service.is_setup_complete()

    assert result is True


# =============================================================================
# SetupService.save_instance_settings
# =============================================================================


@pytest.mark.asyncio
async def test_save_instance_settings_creates_config(
    db_session: AsyncSession,
) -> None:
    """save_instance_settings should create new InstanceConfig."""
    from groundwork.setup.services import SetupService

    service = SetupService(db_session)
    config = await service.save_instance_settings(
        instance_name="My Instance",
        base_url="https://example.com",
    )

    assert config is not None
    assert config.instance_name == "My Instance"
    assert config.base_url == "https://example.com"
    assert config.setup_completed is False


@pytest.mark.asyncio
async def test_save_instance_settings_updates_existing(
    db_session: AsyncSession,
) -> None:
    """save_instance_settings should update existing InstanceConfig."""
    from groundwork.setup.services import SetupService

    # Create existing config
    existing = InstanceConfig(
        instance_name="Old Name",
        base_url="https://old.example.com",
        setup_completed=False,
    )
    db_session.add(existing)
    await db_session.flush()

    service = SetupService(db_session)
    config = await service.save_instance_settings(
        instance_name="New Name",
        base_url="https://new.example.com",
    )

    assert config is not None
    assert config.id == existing.id
    assert config.instance_name == "New Name"
    assert config.base_url == "https://new.example.com"


@pytest.mark.asyncio
async def test_save_instance_settings_handles_race_condition(
    db_session: AsyncSession,
) -> None:
    """save_instance_settings should handle race condition gracefully.

    If a unique constraint violation occurs (another request created the config
    between our check and insert), the method should catch it and update instead.
    """
    from unittest.mock import patch

    from sqlalchemy.exc import IntegrityError

    from groundwork.setup.services import SetupService

    # Create a config that will be "found" on retry after the race condition
    existing = InstanceConfig(
        instance_name="Existing Name",
        base_url="https://existing.example.com",
        setup_completed=False,
    )
    db_session.add(existing)
    await db_session.flush()

    service = SetupService(db_session)

    # Track calls to _get_instance_config
    get_call_count = 0

    async def mock_get_instance_config() -> InstanceConfig | None:
        nonlocal get_call_count
        get_call_count += 1
        if get_call_count == 1:
            return None  # First call: simulate no config exists (race condition)
        # Subsequent calls: return the actual config that was created by "another request"
        result = await db_session.execute(select(InstanceConfig).limit(1))
        return result.scalar_one_or_none()

    # Track calls to db.flush
    flush_call_count = 0
    original_flush = db_session.flush

    async def mock_flush() -> None:
        nonlocal flush_call_count
        flush_call_count += 1
        if flush_call_count == 1:
            # First flush: simulate unique constraint violation (race condition)
            raise IntegrityError(
                statement="INSERT INTO instance_config",
                params={},
                orig=Exception("duplicate key value violates unique constraint"),
            )
        # Subsequent flushes: proceed normally
        return await original_flush()

    # Mock rollback as a no-op since we're not actually in a failed transaction
    async def mock_rollback() -> None:
        pass

    with (
        patch.object(
            service, "_get_instance_config", side_effect=mock_get_instance_config
        ),
        patch.object(db_session, "flush", side_effect=mock_flush),
        patch.object(db_session, "rollback", side_effect=mock_rollback),
    ):
        config = await service.save_instance_settings(
            instance_name="New Name",
            base_url="https://new.example.com",
        )

    # Should have retried and updated the existing config
    assert config is not None
    assert config.instance_name == "New Name"
    assert config.base_url == "https://new.example.com"
    # Verify that _get_instance_config was called twice (initial check + retry after error)
    assert get_call_count == 2
    # Verify that flush was called twice (failed insert + successful update)
    assert flush_call_count == 2


# =============================================================================
# SetupService.create_admin_user
# =============================================================================


@pytest.mark.asyncio
async def test_create_admin_user_creates_role_and_user(
    db_session: AsyncSession,
) -> None:
    """create_admin_user should create Admin role and user."""
    from groundwork.setup.services import SetupService

    service = SetupService(db_session)
    user = await service.create_admin_user(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password="securepassword123",
    )

    assert user is not None
    assert user.email == "admin@example.com"
    assert user.first_name == "Admin"
    assert user.last_name == "User"
    assert verify_password("securepassword123", user.hashed_password)
    assert user.email_verified is True  # Admin is pre-verified


@pytest.mark.asyncio
async def test_create_admin_user_creates_admin_role_with_permissions(
    db_session: AsyncSession,
) -> None:
    """create_admin_user should create Admin role with all permissions."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from groundwork.setup.services import SetupService

    service = SetupService(db_session)
    user = await service.create_admin_user(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password="securepassword123",
    )

    # Verify Admin role exists (with permissions loaded)
    result = await db_session.execute(
        select(Role).where(Role.name == "Admin").options(selectinload(Role.permissions))
    )
    admin_role = result.scalar_one_or_none()

    assert admin_role is not None
    assert admin_role.is_system is True
    assert user.role_id == admin_role.id

    # Verify permissions were created
    permission_codenames = [p.codename for p in admin_role.permissions]
    expected_permissions = [
        "users:create",
        "users:read",
        "users:update",
        "users:delete",
        "roles:manage",
        "settings:manage",
    ]
    for perm in expected_permissions:
        assert perm in permission_codenames


@pytest.mark.asyncio
async def test_create_admin_user_returns_none_for_duplicate(
    db_session: AsyncSession,
) -> None:
    """create_admin_user should return None if admin email already exists."""
    from groundwork.setup.services import SetupService

    service = SetupService(db_session)

    # Create first admin
    await service.create_admin_user(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password="securepassword123",
    )

    # Try to create duplicate
    user = await service.create_admin_user(
        email="admin@example.com",
        first_name="Another",
        last_name="Admin",
        password="differentpassword",
    )

    assert user is None


@pytest.mark.asyncio
async def test_create_admin_user_reuses_existing_admin_role(
    db_session: AsyncSession,
) -> None:
    """create_admin_user should reuse existing Admin role."""
    from sqlalchemy import select

    from groundwork.setup.services import SetupService

    # Create Admin role first
    admin_role = Role(
        name="Admin",
        description="Administrator",
        is_system=True,
    )
    db_session.add(admin_role)
    await db_session.flush()
    original_role_id = admin_role.id

    service = SetupService(db_session)
    user = await service.create_admin_user(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password="securepassword123",
    )

    assert user.role_id == original_role_id

    # Verify only one Admin role exists
    result = await db_session.execute(select(Role).where(Role.name == "Admin"))
    roles = list(result.scalars().all())
    assert len(roles) == 1


# =============================================================================
# SetupService.configure_smtp
# =============================================================================


@pytest.mark.asyncio
async def test_configure_smtp_updates_config(db_session: AsyncSession) -> None:
    """configure_smtp should update InstanceConfig with SMTP settings."""
    from groundwork.setup.services import SetupService

    # Create instance config first
    config = InstanceConfig(
        instance_name="Test Instance",
        base_url="https://example.com",
        setup_completed=False,
    )
    db_session.add(config)
    await db_session.flush()

    service = SetupService(db_session)
    updated = await service.configure_smtp(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="user@example.com",
        smtp_password="password",
        smtp_from_address="noreply@example.com",
    )

    assert updated is not None
    assert updated.smtp_configured is True
    assert updated.smtp_host == "smtp.example.com"
    assert updated.smtp_port == 587
    assert updated.smtp_username == "user@example.com"
    assert updated.smtp_password == "password"
    assert updated.smtp_from_address == "noreply@example.com"


@pytest.mark.asyncio
async def test_configure_smtp_returns_none_without_instance(
    db_session: AsyncSession,
) -> None:
    """configure_smtp should return None if no InstanceConfig exists."""
    from groundwork.setup.services import SetupService

    service = SetupService(db_session)
    result = await service.configure_smtp(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_from_address="noreply@example.com",
    )

    assert result is None


# =============================================================================
# SetupService.skip_smtp
# =============================================================================


@pytest.mark.asyncio
async def test_skip_smtp_leaves_smtp_unconfigured(db_session: AsyncSession) -> None:
    """skip_smtp should leave smtp_configured as False."""
    from groundwork.setup.services import SetupService

    # Create instance config
    config = InstanceConfig(
        instance_name="Test Instance",
        base_url="https://example.com",
        setup_completed=False,
        smtp_configured=False,
    )
    db_session.add(config)
    await db_session.flush()

    service = SetupService(db_session)
    result = await service.skip_smtp()

    assert result is True

    # Verify smtp_configured is still False
    await db_session.refresh(config)
    assert config.smtp_configured is False


@pytest.mark.asyncio
async def test_skip_smtp_returns_false_without_instance(
    db_session: AsyncSession,
) -> None:
    """skip_smtp should return False if no InstanceConfig exists."""
    from groundwork.setup.services import SetupService

    service = SetupService(db_session)
    result = await service.skip_smtp()

    assert result is False


# =============================================================================
# SetupService.complete_setup
# =============================================================================


@pytest.mark.asyncio
async def test_complete_setup_marks_complete(db_session: AsyncSession) -> None:
    """complete_setup should set setup_completed=True."""
    from groundwork.setup.services import SetupService

    # Create instance config
    config = InstanceConfig(
        instance_name="Test Instance",
        base_url="https://example.com",
        setup_completed=False,
    )
    db_session.add(config)

    # Create Admin role and user
    admin_role = Role(
        name="Admin",
        description="Administrator",
        is_system=True,
    )
    db_session.add(admin_role)
    await db_session.flush()

    from groundwork.auth.utils import hash_password

    admin_user = User(
        email="admin@example.com",
        hashed_password=hash_password("password123"),
        first_name="Admin",
        last_name="User",
        role_id=admin_role.id,
    )
    db_session.add(admin_user)
    await db_session.flush()

    service = SetupService(db_session)
    result = await service.complete_setup()

    assert result is not None
    assert result.setup_completed is True


@pytest.mark.asyncio
async def test_complete_setup_fails_without_instance(
    db_session: AsyncSession,
) -> None:
    """complete_setup should return None if no InstanceConfig exists."""
    from groundwork.setup.services import SetupService

    service = SetupService(db_session)
    result = await service.complete_setup()

    assert result is None


@pytest.mark.asyncio
async def test_complete_setup_fails_without_admin(db_session: AsyncSession) -> None:
    """complete_setup should return None if no admin user exists."""
    from groundwork.setup.services import SetupService

    # Create instance config without admin
    config = InstanceConfig(
        instance_name="Test Instance",
        base_url="https://example.com",
        setup_completed=False,
    )
    db_session.add(config)
    await db_session.flush()

    service = SetupService(db_session)
    result = await service.complete_setup()

    assert result is None
