"""Authentication service."""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.models import RefreshToken, User
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
