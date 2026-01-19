"""Profile management API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.dependencies import CurrentUser
from groundwork.core.database import get_db
from groundwork.profile.schemas import (
    AvatarResponse,
    PasswordChange,
    ProfileResponse,
    ProfileUpdate,
    SettingsResponse,
    SettingsUpdate,
)
from groundwork.profile.services import ProfileService

router = APIRouter(tags=["profile"])


@router.get("/", response_model=ProfileResponse)
async def get_profile(
    current_user: CurrentUser,
) -> ProfileResponse:
    """Get current user's profile.

    Returns the authenticated user's profile information.
    """
    return ProfileResponse.model_validate(current_user)


@router.patch("/", response_model=ProfileResponse)
async def update_profile(
    request: ProfileUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProfileResponse:
    """Update current user's profile.

    Allows updating: first_name, last_name, display_name.
    """
    service = ProfileService(db)
    user = await service.update_profile(
        user=current_user,
        first_name=request.first_name,
        last_name=request.last_name,
        display_name=request.display_name,
    )
    return ProfileResponse.model_validate(user)


@router.put("/password")
async def change_password(
    request: PasswordChange,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    """Change current user's password.

    Requires the current password for verification.
    """
    service = ProfileService(db)
    success = await service.change_password(
        user=current_user,
        current_password=request.current_password,
        new_password=request.new_password,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    return {"message": "Password changed successfully"}


@router.put("/avatar", response_model=AvatarResponse)
async def upload_avatar(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: Annotated[UploadFile, File()],
) -> AvatarResponse:
    """Upload avatar for current user.

    Accepts image files (JPEG, PNG, GIF, WebP).
    """
    service = ProfileService(db)
    avatar_path = await service.upload_avatar(
        user=current_user,
        file=file,
    )

    if avatar_path is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only images are allowed.",
        )

    return AvatarResponse(avatar_path=avatar_path)


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(
    current_user: CurrentUser,
) -> SettingsResponse:
    """Get current user's preferences/settings.

    Returns timezone, language, and theme settings.
    """
    return SettingsResponse.model_validate(current_user)


@router.patch("/settings", response_model=SettingsResponse)
async def update_settings(
    request: SettingsUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SettingsResponse:
    """Update current user's preferences/settings.

    Allows updating: timezone, language, theme.
    """
    service = ProfileService(db)
    user = await service.update_settings(
        user=current_user,
        timezone=request.timezone,
        language=request.language,
        theme=request.theme,
    )
    return SettingsResponse.model_validate(user)
