"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Groundwork"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: PostgresDsn
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # Security
    secret_key: str
    access_token_expire_minutes: int = 30

    # Logging
    log_level: str = "INFO"
    log_json: bool = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
