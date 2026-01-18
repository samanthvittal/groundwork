"""Authentication dependencies for FastAPI."""

from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from groundwork.auth.models import User
from groundwork.auth.utils import decode_token
from groundwork.core.database import get_db


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get current authenticated user from access token cookie."""
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


def require_permission(permission: str) -> Callable[[User], User]:
    """Dependency that checks if user has a specific permission."""

    def checker(user: User) -> User:
        if not user.role.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission}",
            )
        return user

    return checker


# Type alias for common dependency
CurrentUser = Annotated[User, Depends(get_current_user)]
