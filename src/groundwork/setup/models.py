"""Setup models."""

from datetime import datetime
from uuid import UUID as PythonUUID
from uuid import uuid4

from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from groundwork.core.database import Base


class InstanceConfig(Base):
    """Instance configuration and setup state."""

    __tablename__ = "instance_config"

    id: Mapped[PythonUUID] = mapped_column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    instance_name: Mapped[str] = mapped_column(String(200))
    base_url: Mapped[str] = mapped_column(String(500))
    setup_completed: Mapped[bool] = mapped_column(default=False)
    smtp_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_port: Mapped[int | None] = mapped_column(nullable=True)
    smtp_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_from_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_configured: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )
