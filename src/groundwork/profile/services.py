"""Profile management service."""

import os

import anyio
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.models import User
from groundwork.auth.utils import hash_password, verify_password

# Directory for avatar uploads
UPLOAD_DIR = "uploads/avatars"

# Maximum avatar file size (5 MB)
MAX_AVATAR_SIZE = 5 * 1024 * 1024

# Allowed image content types
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}

# Magic bytes for validating actual file content (prevents content-type spoofing)
MAGIC_BYTES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/gif": [b"GIF87a", b"GIF89a"],
    "image/webp": [b"RIFF"],  # WebP files start with RIFF
}


class ProfileService:
    """Service for profile management operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    async def update_profile(
        self,
        user: User,
        first_name: str | None = None,
        last_name: str | None = None,
        display_name: str | None = None,
    ) -> User:
        """Update user profile fields.

        Only provided (non-None) fields are updated.
        """
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if display_name is not None:
            user.display_name = display_name

        await self.db.flush()
        return user

    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Change user password.

        Returns True if password was changed, False if current password is incorrect.
        """
        if not verify_password(current_password, user.hashed_password):
            return False

        user.hashed_password = hash_password(new_password)
        await self.db.flush()
        return True

    async def upload_avatar(
        self,
        user: User,
        file: UploadFile,
    ) -> str | None:
        """Upload user avatar.

        Returns the avatar path if successful, None if:
        - File type is not allowed
        - File is too large (>5MB)
        - File content doesn't match claimed type (content-type spoofing)
        """
        # Validate content type header
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            return None

        # Read file content
        content = await file.read()

        # Check file size (prevents resource exhaustion)
        if len(content) > MAX_AVATAR_SIZE:
            return None

        # Validate magic bytes to prevent content-type spoofing
        if not self._validate_magic_bytes(content, file.content_type):
            return None

        # Get file extension from content type
        ext_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
        }
        extension = ext_map.get(file.content_type, ".png")

        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Generate filename using user ID
        filename = f"{user.id}{extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # Save file (using anyio for async file write)
        await anyio.to_thread.run_sync(self._write_file, file_path, content)

        # Update user avatar path
        user.avatar_path = file_path
        await self.db.flush()

        return file_path

    @staticmethod
    def _validate_magic_bytes(content: bytes, content_type: str) -> bool:
        """Validate file content matches the claimed content type.

        Checks magic bytes at the start of the file to prevent content-type spoofing.
        """
        expected_signatures = MAGIC_BYTES.get(content_type, [])
        if not expected_signatures:
            return False

        return any(content.startswith(signature) for signature in expected_signatures)

    @staticmethod
    def _write_file(file_path: str, content: bytes) -> None:
        """Write content to file (blocking operation, called via anyio)."""
        with open(file_path, "wb") as f:
            f.write(content)

    async def update_settings(
        self,
        user: User,
        timezone: str | None = None,
        language: str | None = None,
        theme: str | None = None,
    ) -> User:
        """Update user preferences/settings.

        Only provided (non-None) fields are updated.
        """
        if timezone is not None:
            user.timezone = timezone
        if language is not None:
            user.language = language
        if theme is not None:
            user.theme = theme

        await self.db.flush()
        return user
