"""Tests for profile service."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from groundwork.auth.models import User


@pytest.fixture
def mock_db() -> AsyncMock:
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_role() -> MagicMock:
    """Create a mock role."""
    role = MagicMock()
    role.id = uuid4()
    role.name = "user"
    return role


@pytest.fixture
def mock_user(mock_role: MagicMock) -> MagicMock:
    """Create a mock user."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.display_name = "TestDisplay"
    user.avatar_path = None
    user.is_active = True
    user.email_verified = True
    user.timezone = "UTC"
    user.language = "en"
    user.theme = "system"
    user.hashed_password = "$argon2id$v=19$m=65536,t=3,p=4$somesalt$somehash"
    user.created_at = datetime(2024, 1, 1, 0, 0, 0)
    user.updated_at = datetime(2024, 1, 1, 0, 0, 0)
    user.last_login_at = None
    user.role_id = mock_role.id
    user.role = mock_role
    return user


# =============================================================================
# ProfileService.update_profile
# =============================================================================


@pytest.mark.asyncio
async def test_update_profile_updates_first_name(
    mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """update_profile should update first_name."""
    from groundwork.profile.services import ProfileService

    service = ProfileService(mock_db)

    result = await service.update_profile(
        user=mock_user,
        first_name="NewFirst",
    )

    assert mock_user.first_name == "NewFirst"
    mock_db.flush.assert_called_once()
    assert result == mock_user


@pytest.mark.asyncio
async def test_update_profile_updates_last_name(
    mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """update_profile should update last_name."""
    from groundwork.profile.services import ProfileService

    service = ProfileService(mock_db)

    result = await service.update_profile(
        user=mock_user,
        last_name="NewLast",
    )

    assert mock_user.last_name == "NewLast"
    mock_db.flush.assert_called_once()
    assert result == mock_user


@pytest.mark.asyncio
async def test_update_profile_updates_display_name(
    mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """update_profile should update display_name."""
    from groundwork.profile.services import ProfileService

    service = ProfileService(mock_db)

    result = await service.update_profile(
        user=mock_user,
        display_name="NewDisplayName",
    )

    assert mock_user.display_name == "NewDisplayName"
    mock_db.flush.assert_called_once()
    assert result == mock_user


@pytest.mark.asyncio
async def test_update_profile_ignores_none_values(
    mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """update_profile should not update fields with None values."""
    from groundwork.profile.services import ProfileService

    service = ProfileService(mock_db)
    original_first_name = mock_user.first_name

    result = await service.update_profile(
        user=mock_user,
        first_name=None,
        last_name=None,
        display_name=None,
    )

    # first_name should remain unchanged
    assert mock_user.first_name == original_first_name
    assert result == mock_user


# =============================================================================
# ProfileService.change_password
# =============================================================================


@pytest.mark.asyncio
async def test_change_password_success_when_current_password_correct(
    mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """change_password should return True when current password is correct."""
    from groundwork.profile.services import ProfileService

    service = ProfileService(mock_db)

    with (
        patch("groundwork.profile.services.verify_password", return_value=True),
        patch("groundwork.profile.services.hash_password", return_value="new_hash"),
    ):
        result = await service.change_password(
            user=mock_user,
            current_password="oldpassword123",
            new_password="newpassword123",
        )

    assert result is True
    assert mock_user.hashed_password == "new_hash"
    mock_db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_change_password_returns_false_when_current_password_wrong(
    mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """change_password should return False when current password is wrong."""
    from groundwork.profile.services import ProfileService

    service = ProfileService(mock_db)
    original_hash = mock_user.hashed_password

    with patch("groundwork.profile.services.verify_password", return_value=False):
        result = await service.change_password(
            user=mock_user,
            current_password="wrongpassword",
            new_password="newpassword123",
        )

    assert result is False
    assert mock_user.hashed_password == original_hash
    mock_db.flush.assert_not_called()


# =============================================================================
# ProfileService.upload_avatar
# =============================================================================


@pytest.mark.asyncio
async def test_upload_avatar_saves_file_and_updates_user(
    mock_db: AsyncMock, mock_user: MagicMock, tmp_path: str
) -> None:
    """upload_avatar should save file and update user.avatar_path."""
    from groundwork.profile.services import ProfileService

    service = ProfileService(mock_db)

    # Create mock file
    mock_file = MagicMock()
    mock_file.filename = "avatar.png"
    mock_file.content_type = "image/png"
    mock_file.read = AsyncMock(return_value=b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

    with (
        patch("groundwork.profile.services.UPLOAD_DIR", str(tmp_path)),
        patch("os.makedirs"),
        patch("anyio.to_thread.run_sync", AsyncMock()),
    ):
        result = await service.upload_avatar(
            user=mock_user,
            file=mock_file,
        )

    assert result is not None
    assert str(mock_user.id) in result
    assert ".png" in result
    mock_db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_upload_avatar_returns_none_for_invalid_content_type(
    mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """upload_avatar should return None for non-image content types."""
    from groundwork.profile.services import ProfileService

    service = ProfileService(mock_db)

    mock_file = MagicMock()
    mock_file.filename = "document.txt"
    mock_file.content_type = "text/plain"

    result = await service.upload_avatar(
        user=mock_user,
        file=mock_file,
    )

    assert result is None
    mock_db.flush.assert_not_called()


@pytest.mark.asyncio
async def test_upload_avatar_accepts_jpeg(
    mock_db: AsyncMock, mock_user: MagicMock, tmp_path: str
) -> None:
    """upload_avatar should accept JPEG images."""
    from groundwork.profile.services import ProfileService

    service = ProfileService(mock_db)

    mock_file = MagicMock()
    mock_file.filename = "avatar.jpg"
    mock_file.content_type = "image/jpeg"
    mock_file.read = AsyncMock(return_value=b"\xff\xd8\xff" + b"\x00" * 100)

    with (
        patch("groundwork.profile.services.UPLOAD_DIR", str(tmp_path)),
        patch("os.makedirs"),
        patch("anyio.to_thread.run_sync", AsyncMock()),
    ):
        result = await service.upload_avatar(
            user=mock_user,
            file=mock_file,
        )

    assert result is not None
    assert ".jpg" in result


@pytest.mark.asyncio
async def test_upload_avatar_rejects_file_too_large(
    mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """upload_avatar should return None for files exceeding size limit."""
    from groundwork.profile.services import MAX_AVATAR_SIZE, ProfileService

    service = ProfileService(mock_db)

    # Create file larger than MAX_AVATAR_SIZE
    large_content = b"\x89PNG\r\n\x1a\n" + (b"\x00" * (MAX_AVATAR_SIZE + 1))

    mock_file = MagicMock()
    mock_file.filename = "large_avatar.png"
    mock_file.content_type = "image/png"
    mock_file.read = AsyncMock(return_value=large_content)

    result = await service.upload_avatar(
        user=mock_user,
        file=mock_file,
    )

    assert result is None
    mock_db.flush.assert_not_called()


@pytest.mark.asyncio
async def test_upload_avatar_rejects_spoofed_content_type(
    mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """upload_avatar should return None when magic bytes don't match content type."""
    from groundwork.profile.services import ProfileService

    service = ProfileService(mock_db)

    # File claims to be PNG but has HTML content (XSS attack attempt)
    mock_file = MagicMock()
    mock_file.filename = "fake.png"
    mock_file.content_type = "image/png"
    mock_file.read = AsyncMock(
        return_value=b"<html><script>alert('xss')</script></html>"
    )

    result = await service.upload_avatar(
        user=mock_user,
        file=mock_file,
    )

    assert result is None
    mock_db.flush.assert_not_called()


@pytest.mark.asyncio
async def test_upload_avatar_accepts_gif(
    mock_db: AsyncMock, mock_user: MagicMock, tmp_path: str
) -> None:
    """upload_avatar should accept GIF images with correct magic bytes."""
    from groundwork.profile.services import ProfileService

    service = ProfileService(mock_db)

    mock_file = MagicMock()
    mock_file.filename = "avatar.gif"
    mock_file.content_type = "image/gif"
    mock_file.read = AsyncMock(return_value=b"GIF89a" + b"\x00" * 100)

    with (
        patch("groundwork.profile.services.UPLOAD_DIR", str(tmp_path)),
        patch("os.makedirs"),
        patch("anyio.to_thread.run_sync", AsyncMock()),
    ):
        result = await service.upload_avatar(
            user=mock_user,
            file=mock_file,
        )

    assert result is not None
    assert ".gif" in result


# =============================================================================
# ProfileService.update_settings
# =============================================================================


@pytest.mark.asyncio
async def test_update_settings_updates_timezone(
    mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """update_settings should update timezone."""
    from groundwork.profile.services import ProfileService

    service = ProfileService(mock_db)

    result = await service.update_settings(
        user=mock_user,
        timezone="America/New_York",
    )

    assert mock_user.timezone == "America/New_York"
    mock_db.flush.assert_called_once()
    assert result == mock_user


@pytest.mark.asyncio
async def test_update_settings_updates_language(
    mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """update_settings should update language."""
    from groundwork.profile.services import ProfileService

    service = ProfileService(mock_db)

    result = await service.update_settings(
        user=mock_user,
        language="es",
    )

    assert mock_user.language == "es"
    mock_db.flush.assert_called_once()
    assert result == mock_user


@pytest.mark.asyncio
async def test_update_settings_updates_theme(
    mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """update_settings should update theme."""
    from groundwork.profile.services import ProfileService

    service = ProfileService(mock_db)

    result = await service.update_settings(
        user=mock_user,
        theme="dark",
    )

    assert mock_user.theme == "dark"
    mock_db.flush.assert_called_once()
    assert result == mock_user


@pytest.mark.asyncio
async def test_update_settings_updates_multiple_fields(
    mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """update_settings should update multiple fields at once."""
    from groundwork.profile.services import ProfileService

    service = ProfileService(mock_db)

    result = await service.update_settings(
        user=mock_user,
        timezone="Europe/London",
        language="fr",
        theme="light",
    )

    assert mock_user.timezone == "Europe/London"
    assert mock_user.language == "fr"
    assert mock_user.theme == "light"
    mock_db.flush.assert_called_once()
    assert result == mock_user


@pytest.mark.asyncio
async def test_update_settings_ignores_none_values(
    mock_db: AsyncMock, mock_user: MagicMock
) -> None:
    """update_settings should not update fields with None values."""
    from groundwork.profile.services import ProfileService

    service = ProfileService(mock_db)
    original_timezone = mock_user.timezone

    result = await service.update_settings(
        user=mock_user,
        timezone=None,
        language=None,
        theme=None,
    )

    assert mock_user.timezone == original_timezone
    assert result == mock_user
