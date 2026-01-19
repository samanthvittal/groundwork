"""Authentication view routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.dependencies import get_current_user_optional
from groundwork.auth.models import User
from groundwork.auth.services import AuthService
from groundwork.core.database import get_db
from groundwork.core.templates import get_templates
from groundwork.setup.services import SetupService

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_form(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> Response:
    """Login page."""
    if current_user:
        return RedirectResponse(url="/users", status_code=303)

    setup_service = SetupService(db)
    config = await setup_service._get_instance_config()

    templates = get_templates()
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={
            "smtp_configured": config.smtp_configured if config else False,
        },
    )


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
) -> Response:
    """Process login."""
    auth_service = AuthService(db)
    setup_service = SetupService(db)
    config = await setup_service._get_instance_config()
    templates = get_templates()

    result = await auth_service.login(email, password)

    if result is None:
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={
                "error": "Invalid email or password",
                "email": email,
                "smtp_configured": config.smtp_configured if config else False,
            },
        )

    # Set cookies and redirect
    response = RedirectResponse(url="/users", status_code=303)
    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        max_age=900,  # 15 minutes
    )
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        max_age=604800,  # 7 days
    )
    return response


@router.post("/logout")
async def logout(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Logout and clear cookies."""
    auth_service = AuthService(db)

    # Try to revoke refresh token
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await auth_service.logout(refresh_token)

    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_form(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Password reset request page."""
    setup_service = SetupService(db)
    config = await setup_service._get_instance_config()

    # If SMTP not configured, redirect to login
    if not config or not config.smtp_configured:
        return RedirectResponse(url="/login", status_code=303)

    templates = get_templates()
    return templates.TemplateResponse(
        request=request,
        name="auth/password_reset.html",
    )


@router.post("/forgot-password", response_class=HTMLResponse)
async def forgot_password_submit(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    email: Annotated[str, Form()],
) -> Response:
    """Process password reset request."""
    auth_service = AuthService(db)

    # Always show success to prevent email enumeration
    await auth_service.request_password_reset(email)

    templates = get_templates()
    return templates.TemplateResponse(
        request=request,
        name="auth/password_reset.html",
        context={
            "success": True,
            "email": email,
        },
    )


@router.get("/reset-password/{token}", response_class=HTMLResponse)
async def reset_password_form(
    request: Request,
    token: str,
) -> Response:
    """Password reset confirmation page."""
    templates = get_templates()
    return templates.TemplateResponse(
        request=request,
        name="auth/password_reset_confirm.html",
        context={"token": token},
    )


@router.post("/reset-password/{token}", response_class=HTMLResponse)
async def reset_password_submit(
    request: Request,
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    password: Annotated[str, Form()],
    password_confirm: Annotated[str, Form()],
) -> Response:
    """Process password reset."""
    templates = get_templates()

    if password != password_confirm:
        return templates.TemplateResponse(
            request=request,
            name="auth/password_reset_confirm.html",
            context={
                "token": token,
                "error": "Passwords do not match",
            },
        )

    if len(password) < 8:
        return templates.TemplateResponse(
            request=request,
            name="auth/password_reset_confirm.html",
            context={
                "token": token,
                "error": "Password must be at least 8 characters",
            },
        )

    auth_service = AuthService(db)
    success = await auth_service.confirm_password_reset(token, password)

    if not success:
        return templates.TemplateResponse(
            request=request,
            name="auth/password_reset_confirm.html",
            context={"invalid_token": True},
        )

    return templates.TemplateResponse(
        request=request,
        name="auth/password_reset_confirm.html",
        context={"success": True},
    )
