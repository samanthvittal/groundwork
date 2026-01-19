"""Authentication API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.dependencies import get_current_user
from groundwork.auth.models import User
from groundwork.auth.schemas import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenResponse,
    UserResponse,
)
from groundwork.auth.services import AuthService
from groundwork.core.database import get_db

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Authenticate user and set cookies."""
    service = AuthService(db)
    result = await service.login(request.email, request.password)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Set HTTP-only cookies
    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=900,  # 15 minutes
    )
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=604800,  # 7 days
    )

    return TokenResponse(
        user=UserResponse.model_validate(result["user"]),
        csrf_token=result["csrf_token"],
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Logout user and clear cookies."""
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        service = AuthService(db)
        await service.logout(refresh_token)

    # Clear cookies
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Refresh access token using refresh token cookie."""
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )

    service = AuthService(db)
    result = await service.refresh_access_token(refresh_token)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Update access token cookie
    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=900,
    )

    return TokenResponse(
        user=UserResponse.model_validate(result["user"]),
        csrf_token=result["csrf_token"],
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Get current authenticated user."""
    return UserResponse.model_validate(current_user)


@router.post("/password-reset")
async def request_password_reset(
    request: PasswordResetRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    """Request password reset email.

    Always returns success to prevent email enumeration.
    """
    service = AuthService(db)
    # In production, send email with the returned token
    # For now, just call the service (result intentionally unused to prevent enumeration)
    await service.request_password_reset(request.email)

    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a reset link has been sent"}


@router.put("/password-reset/{token}")
async def confirm_password_reset(
    token: str,
    request: PasswordResetConfirm,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    """Reset password with token."""
    service = AuthService(db)
    success = await service.confirm_password_reset(token, request.new_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    return {"message": "Password reset successfully"}
