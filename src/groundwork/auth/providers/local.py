"""Local authentication provider."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.models import User
from groundwork.auth.providers.base import AuthProvider
from groundwork.auth.utils import hash_password, verify_password


class LocalAuthProvider(AuthProvider):
    """Authentication provider using local database."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    async def authenticate(self, email: str, password: str) -> User | None:
        """Authenticate user with email and password."""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None:
            # Perform dummy verification to prevent timing attacks
            verify_password(password, hash_password("dummy"))
            return None

        if not user.is_active:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    async def create_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role_id: UUID,
    ) -> User:
        """Create a new user with hashed password."""
        user = User(
            email=email,
            hashed_password=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role_id=role_id,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def change_password(self, user: User, new_password: str) -> None:
        """Change user's password."""
        user.hashed_password = hash_password(new_password)
        await self.db.flush()

    async def verify_email(self, user: User) -> None:
        """Mark user's email as verified."""
        user.email_verified = True
        await self.db.flush()
