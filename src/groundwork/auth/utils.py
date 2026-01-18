"""Authentication utilities."""

from datetime import UTC, datetime, timedelta
from typing import Any, cast

from jose import JWTError, jwt
from passlib.context import CryptContext

from groundwork.core.config import get_settings

# Argon2 password hashing
pwd_context: CryptContext = CryptContext(schemes=["argon2"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """Hash a password using Argon2."""
    result: str = pwd_context.hash(password)
    return result


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    result: bool = pwd_context.verify(plain_password, hashed_password)
    return result


def create_access_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    settings = get_settings()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "access",
    }
    return cast(str, jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM))


def create_refresh_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Create a JWT refresh token."""
    settings = get_settings()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
    }
    return cast(str, jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM))


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return cast(dict[str, Any], payload)
    except JWTError:
        return None
