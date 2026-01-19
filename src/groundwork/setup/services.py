"""Setup wizard service."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from groundwork.auth.models import Permission, Role, User
from groundwork.auth.utils import hash_password
from groundwork.setup.models import InstanceConfig

# Default permissions for Admin role
DEFAULT_ADMIN_PERMISSIONS = [
    ("users:create", "Can create users"),
    ("users:read", "Can read users"),
    ("users:update", "Can update users"),
    ("users:delete", "Can delete users"),
    ("roles:manage", "Can manage roles and permissions"),
    ("settings:manage", "Can manage system settings"),
]


class SetupService:
    """Service for setup wizard operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize with database session."""
        self.db = db

    async def get_setup_status(self) -> dict[str, Any]:
        """Get the current setup status.

        Returns a dict with:
        - setup_completed: bool
        - current_step: str | None (welcome, instance, admin, smtp, complete)
        """
        # Get instance config
        config = await self._get_instance_config()

        if config is None:
            return {"setup_completed": False, "current_step": "welcome"}

        if config.setup_completed:
            return {"setup_completed": True, "current_step": "complete"}

        # Check if admin exists
        admin_exists = await self._admin_exists()
        if not admin_exists:
            return {"setup_completed": False, "current_step": "admin"}

        # Check SMTP status - if we have admin but not complete, we're at SMTP step
        return {"setup_completed": False, "current_step": "smtp"}

    async def is_setup_complete(self) -> bool:
        """Check if setup has been completed."""
        config = await self._get_instance_config()
        return config is not None and config.setup_completed

    async def save_instance_settings(
        self,
        instance_name: str,
        base_url: str,
    ) -> InstanceConfig:
        """Create or update instance settings.

        Args:
            instance_name: Name of the instance.
            base_url: Base URL for the instance.

        Returns:
            The created or updated InstanceConfig.

        Note:
            This method handles race conditions where two requests might try to
            create the config simultaneously. If an IntegrityError occurs during
            insert, it catches the error and retries as an update operation.
        """
        config = await self._get_instance_config()

        if config is None:
            config = InstanceConfig(
                instance_name=instance_name,
                base_url=base_url,
                setup_completed=False,
                smtp_configured=False,
            )
            self.db.add(config)
            try:
                await self.db.flush()
            except IntegrityError:
                # Race condition: another request created the config between
                # our check and insert. Rollback the failed insert and retry
                # as an update operation.
                await self.db.rollback()
                config = await self._get_instance_config()
                if config is None:
                    # This shouldn't happen, but re-raise if it does
                    raise
                config.instance_name = instance_name
                config.base_url = base_url
                await self.db.flush()
        else:
            config.instance_name = instance_name
            config.base_url = base_url
            await self.db.flush()

        return config

    async def create_admin_user(
        self,
        email: str,
        first_name: str,
        last_name: str,
        password: str,
    ) -> User | None:
        """Create the initial admin user.

        Creates Admin role with all permissions if it doesn't exist.

        Args:
            email: Admin email address.
            first_name: Admin first name.
            last_name: Admin last name.
            password: Admin password.

        Returns:
            The created User, or None if email already exists.
        """
        # Check if user with this email already exists
        existing_user = await self.db.execute(select(User).where(User.email == email))
        if existing_user.scalar_one_or_none() is not None:
            return None

        # Get or create Admin role
        admin_role = await self._get_or_create_admin_role()

        # Create admin user
        user = User(
            email=email,
            hashed_password=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role_id=admin_role.id,
            is_active=True,
            email_verified=True,  # Admin is pre-verified
        )
        self.db.add(user)
        await self.db.flush()

        return user

    async def configure_smtp(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_from_address: str,
        smtp_username: str | None = None,
        smtp_password: str | None = None,
    ) -> InstanceConfig | None:
        """Configure SMTP settings.

        Args:
            smtp_host: SMTP server hostname.
            smtp_port: SMTP server port.
            smtp_from_address: From address for emails.
            smtp_username: Optional SMTP username.
            smtp_password: Optional SMTP password.

        Returns:
            The updated InstanceConfig, or None if no config exists.
        """
        config = await self._get_instance_config()
        if config is None:
            return None

        config.smtp_host = smtp_host
        config.smtp_port = smtp_port
        config.smtp_username = smtp_username
        # TODO: SECURITY - smtp_password is currently stored in plaintext.
        # This should be encrypted at rest using application-level encryption
        # (e.g., Fernet symmetric encryption with a key derived from SECRET_KEY).
        # See: https://cryptography.io/en/latest/fernet/
        config.smtp_password = smtp_password
        config.smtp_from_address = smtp_from_address
        config.smtp_configured = True

        await self.db.flush()
        return config

    async def skip_smtp(self) -> bool:
        """Mark SMTP configuration as skipped.

        Returns:
            True if successful, False if no InstanceConfig exists.
        """
        config = await self._get_instance_config()
        if config is None:
            return False

        # smtp_configured stays False, no changes needed
        await self.db.flush()
        return True

    async def complete_setup(self) -> InstanceConfig | None:
        """Complete the setup process.

        Requires instance settings and admin user to be configured.

        Returns:
            The updated InstanceConfig, or None if prerequisites not met.
        """
        config = await self._get_instance_config()
        if config is None:
            return None

        # Check that admin exists
        admin_exists = await self._admin_exists()
        if not admin_exists:
            return None

        config.setup_completed = True
        await self.db.flush()
        return config

    async def _get_instance_config(self) -> InstanceConfig | None:
        """Get the singleton InstanceConfig."""
        result = await self.db.execute(select(InstanceConfig).limit(1))
        return result.scalar_one_or_none()

    async def _admin_exists(self) -> bool:
        """Check if an admin user exists."""
        # Check for Admin role and any user with that role
        result = await self.db.execute(
            select(Role).where(Role.name == "Admin").options(selectinload(Role.users))
        )
        admin_role = result.scalar_one_or_none()
        if admin_role is None:
            return False
        return len(admin_role.users) > 0

    async def _get_or_create_admin_role(self) -> Role:
        """Get existing Admin role or create it with default permissions."""
        # Check if Admin role exists
        result = await self.db.execute(
            select(Role)
            .where(Role.name == "Admin")
            .options(selectinload(Role.permissions))
        )
        admin_role = result.scalar_one_or_none()

        if admin_role is not None:
            return admin_role

        # Create permissions
        permissions = []
        for codename, description in DEFAULT_ADMIN_PERMISSIONS:
            # Check if permission already exists
            perm_result = await self.db.execute(
                select(Permission).where(Permission.codename == codename)
            )
            permission = perm_result.scalar_one_or_none()

            if permission is None:
                permission = Permission(codename=codename, description=description)
                self.db.add(permission)

            permissions.append(permission)

        await self.db.flush()

        # Create Admin role
        admin_role = Role(
            name="Admin",
            description="Administrator with full access",
            is_system=True,
            permissions=permissions,
        )
        self.db.add(admin_role)
        await self.db.flush()

        return admin_role
