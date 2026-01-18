"""Base authentication provider."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from groundwork.auth.models import User


class AuthProvider(ABC):
    """Abstract base class for authentication providers."""

    @abstractmethod
    async def authenticate(self, email: str, password: str) -> "User | None":
        """Authenticate user with email and password.

        Returns User if credentials are valid, None otherwise.
        """
        ...

    @abstractmethod
    async def create_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role_id: str,
    ) -> "User":
        """Create a new user."""
        ...

    @abstractmethod
    async def change_password(self, user: "User", new_password: str) -> None:
        """Change user's password."""
        ...

    @abstractmethod
    async def verify_email(self, user: "User") -> None:
        """Mark user's email as verified."""
        ...
