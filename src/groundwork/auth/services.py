"""Authentication service."""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.models import PasswordResetToken, RefreshToken, User
from groundwork.auth.providers.local import LocalAuthProvider
from groundwork.auth.utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from groundwork.core.config import get_settings


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db
        self.provider = LocalAuthProvider(db)

    async def login(self, email: str, password: str) -> dict[str, Any] | None:
        """Authenticate user and return tokens."""
        user = await self.provider.authenticate(email, password)
        if user is None:
            return None

        # Update last login
        user.last_login_at = datetime.now(UTC)

        # Generate tokens
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))

        # Store refresh token hash
        settings = get_settings()
        token_record = RefreshToken(
            user_id=user.id,
            token_hash=hash_password(refresh_token),
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.refresh_token_expire_days),
        )
        self.db.add(token_record)
        await self.db.flush()

        # Generate CSRF token
        csrf_token = secrets.token_urlsafe(32)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "csrf_token": csrf_token,
            "user": user,
        }

    async def logout(self, refresh_token: str) -> bool:
        """Revoke refresh token."""
        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            return False

        user_id = payload.get("sub")
        if not user_id:
            return False

        # Find the specific token by verifying its hash
        result = await self.db.execute(
            select(RefreshToken)
            .where(RefreshToken.user_id == UUID(user_id))
            .where(RefreshToken.revoked_at.is_(None))
        )
        tokens = result.scalars().all()

        # Find the specific token matching the hash
        valid_token = None
        for token in tokens:
            if verify_password(refresh_token, token.token_hash):
                valid_token = token
                break

        if valid_token is None:
            return False

        # Revoke only the specific token
        valid_token.revoked_at = datetime.now(UTC)
        await self.db.flush()
        return True

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any] | None:
        """Generate new access token from refresh token."""
        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        # Validate refresh token exists in database, is not revoked, and not expired
        result = await self.db.execute(
            select(RefreshToken)
            .where(RefreshToken.user_id == UUID(user_id))
            .where(RefreshToken.revoked_at.is_(None))
            .where(RefreshToken.expires_at > datetime.now(UTC))
        )
        tokens = result.scalars().all()

        valid_token = None
        for token in tokens:
            if verify_password(refresh_token, token.token_hash):
                valid_token = token
                break

        if valid_token is None:
            return None  # Token not found, expired, or revoked

        # Verify user exists and is active
        user_result = await self.db.execute(
            select(User).where(User.id == UUID(user_id))
        )
        user = user_result.scalar_one_or_none()

        if user is None or not user.is_active:
            return None

        # Generate new access token
        access_token = create_access_token(str(user.id))
        csrf_token = secrets.token_urlsafe(32)

        return {
            "access_token": access_token,
            "csrf_token": csrf_token,
            "user": user,
        }

    async def request_password_reset(self, email: str) -> str | None:
        """Generate password reset token for email.

        Returns the raw token (to be sent via email) or None if user not found.
        Token format: {selector}.{validator}
        - selector: 16 chars, stored unhashed for O(1) lookup
        - validator: 32 chars, hashed for security
        """
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            return None

        # Generate selector (for lookup) and validator (for verification)
        selector = secrets.token_urlsafe(16)[:16]  # Ensure exactly 16 chars
        validator = secrets.token_urlsafe(32)

        # Store selector unhashed (for lookup), validator hashed (for security)
        token_record = PasswordResetToken(
            user_id=user.id,
            token_selector=selector,
            token_hash=hash_password(validator),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        self.db.add(token_record)
        await self.db.flush()

        # Return combined token
        return f"{selector}.{validator}"

    async def confirm_password_reset(self, token: str, new_password: str) -> bool:
        """Reset password using token.

        Returns True if successful, False if token invalid/expired.
        Token format: {selector}.{validator}
        Uses O(1) lookup by selector, then verifies validator hash.
        """
        # Parse token into selector and validator
        if "." not in token:
            return False

        parts = token.split(".", 1)
        if len(parts) != 2:
            return False

        selector, validator = parts

        # O(1) lookup by selector - prevents timing attacks
        reset_token_result = await self.db.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.token_selector == selector)
            .where(PasswordResetToken.used_at.is_(None))
            .where(PasswordResetToken.expires_at > datetime.now(UTC))
        )
        reset_token = reset_token_result.scalar_one_or_none()

        if reset_token is None:
            return False

        # Verify validator against stored hash
        if not verify_password(validator, reset_token.token_hash):
            return False

        # Get user and update password
        user_result = await self.db.execute(
            select(User).where(User.id == reset_token.user_id)
        )
        user = user_result.scalar_one_or_none()

        if user is None:
            return False

        # Update password
        user.hashed_password = hash_password(new_password)

        # Mark token as used
        reset_token.used_at = datetime.now(UTC)

        # Revoke all refresh tokens for user
        refresh_token_result = await self.db.execute(
            select(RefreshToken)
            .where(RefreshToken.user_id == user.id)
            .where(RefreshToken.revoked_at.is_(None))
        )
        for rt in refresh_token_result.scalars():
            rt.revoked_at = datetime.now(UTC)

        await self.db.flush()
        return True
