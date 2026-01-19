"""User management service."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from groundwork.auth.models import User
from groundwork.auth.utils import hash_password


class UserService:
    """Service for user management operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    async def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """List users with pagination."""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.role))
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at)
        )
        return list(result.scalars().all())

    async def get_user(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).options(selectinload(User.role)).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role_id: UUID,
        display_name: str | None = None,
        timezone: str = "UTC",
        language: str = "en",
        theme: str = "system",
    ) -> User | None:
        """Create a new user.

        Returns the created user, or None if email already exists.
        """
        # Check if email already exists
        existing = await self.db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none() is not None:
            return None

        user = User(
            email=email,
            hashed_password=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role_id=role_id,
            display_name=display_name,
            timezone=timezone,
            language=language,
            theme=theme,
            is_active=True,
            email_verified=False,
        )
        self.db.add(user)
        await self.db.flush()

        # Reload with role relationship
        return await self.get_user(user.id)

    async def update_user(
        self,
        user_id: UUID,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        role_id: UUID | None = None,
        display_name: str | None = None,
        timezone: str | None = None,
        language: str | None = None,
        theme: str | None = None,
        is_active: bool | None = None,
        email_verified: bool | None = None,
    ) -> User | None:
        """Update user fields.

        Returns updated user, or None if user not found.
        Only provided (non-None) fields are updated.
        """
        user = await self.get_user(user_id)
        if user is None:
            return None

        if email is not None:
            user.email = email
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if role_id is not None:
            user.role_id = role_id
        if display_name is not None:
            user.display_name = display_name
        if timezone is not None:
            user.timezone = timezone
        if language is not None:
            user.language = language
        if theme is not None:
            user.theme = theme
        if is_active is not None:
            user.is_active = is_active
        if email_verified is not None:
            user.email_verified = email_verified

        await self.db.flush()
        return user

    async def deactivate_user(self, user_id: UUID) -> bool:
        """Deactivate user (soft delete).

        Returns True if user was deactivated, False if user not found.
        """
        user = await self.get_user(user_id)
        if user is None:
            return False

        user.is_active = False
        await self.db.flush()
        return True

    async def reset_password(self, user_id: UUID, new_password: str) -> bool:
        """Reset user password (admin action).

        Does NOT require old password. Returns True if successful, False if user not found.
        """
        user = await self.get_user(user_id)
        if user is None:
            return False

        user.hashed_password = hash_password(new_password)
        await self.db.flush()
        return True
