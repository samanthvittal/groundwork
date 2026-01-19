"""User management API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.dependencies import CurrentUser, require_permission
from groundwork.auth.models import User
from groundwork.core.database import get_db
from groundwork.users.schemas import PasswordReset, UserCreate, UserResponse, UserUpdate
from groundwork.users.services import UserService

router = APIRouter(tags=["users"])


# Permission check functions that wrap require_permission with CurrentUser dependency
def check_users_read(current_user: CurrentUser) -> User:
    """Check users:read permission."""
    return require_permission("users:read")(current_user)


def check_users_create(current_user: CurrentUser) -> User:
    """Check users:create permission."""
    return require_permission("users:create")(current_user)


def check_users_update(current_user: CurrentUser) -> User:
    """Check users:update permission."""
    return require_permission("users:update")(current_user)


def check_users_delete(current_user: CurrentUser) -> User:
    """Check users:delete permission."""
    return require_permission("users:delete")(current_user)


def parse_uuid(user_id: str) -> UUID:
    """Parse and validate UUID, raise 404 for invalid UUIDs."""
    try:
        return UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ) from None


@router.get("/", response_model=list[UserResponse])
async def list_users(
    _: Annotated[User, Depends(check_users_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
) -> list[UserResponse]:
    """List users with pagination.

    Requires `users:read` permission.
    """
    service = UserService(db)
    users = await service.list_users(skip=skip, limit=limit)
    return [UserResponse.model_validate(user) for user in users]


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreate,
    _: Annotated[User, Depends(check_users_create)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Create a new user.

    Requires `users:create` permission.
    """
    service = UserService(db)
    user = await service.create_user(
        email=request.email,
        password=request.password,
        first_name=request.first_name,
        last_name=request.last_name,
        role_id=request.role_id,
        display_name=request.display_name,
        timezone=request.timezone,
        language=request.language,
        theme=request.theme,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    _: Annotated[User, Depends(check_users_read)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Get user by ID.

    Requires `users:read` permission.
    """
    uuid = parse_uuid(user_id)
    service = UserService(db)
    user = await service.get_user(uuid)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdate,
    _: Annotated[User, Depends(check_users_update)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Update user fields.

    Requires `users:update` permission.
    """
    uuid = parse_uuid(user_id)
    service = UserService(db)
    user = await service.update_user(
        user_id=uuid,
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        role_id=request.role_id,
        display_name=request.display_name,
        timezone=request.timezone,
        language=request.language,
        theme=request.theme,
        is_active=request.is_active,
        email_verified=request.email_verified,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    _: Annotated[User, Depends(check_users_delete)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Deactivate user (soft delete).

    Sets `is_active = False` instead of deleting.
    Requires `users:delete` permission.
    """
    uuid = parse_uuid(user_id)
    service = UserService(db)
    result = await service.deactivate_user(uuid)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{user_id}/password")
async def reset_password(
    user_id: str,
    request: PasswordReset,
    _: Annotated[User, Depends(check_users_update)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    """Reset user password (admin action).

    Does NOT require old password.
    Requires `users:update` permission.
    """
    uuid = parse_uuid(user_id)
    service = UserService(db)
    result = await service.reset_password(uuid, request.new_password)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": "Password reset successfully"}
