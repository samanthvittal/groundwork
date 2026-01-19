"""Profile view routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.dependencies import get_current_user
from groundwork.auth.models import User
from groundwork.auth.utils import hash_password, verify_password
from groundwork.core.database import get_db
from groundwork.core.templates import get_templates

router = APIRouter()


@router.get("/profile", response_class=HTMLResponse)
async def profile_view(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Profile view page."""
    templates = get_templates()
    return templates.TemplateResponse(
        request=request,
        name="profile/view.html",
        context={"user": current_user},
    )


@router.get("/profile/edit", response_class=HTMLResponse)
async def profile_edit_form(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Profile edit form."""
    templates = get_templates()
    return templates.TemplateResponse(
        request=request,
        name="profile/edit.html",
        context={"user": current_user},
    )


@router.post("/profile/edit", response_class=HTMLResponse)
async def profile_edit_submit(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    first_name: Annotated[str, Form()],
    last_name: Annotated[str, Form()],
    display_name: Annotated[str | None, Form()] = None,
) -> Response:
    """Process profile edit."""
    templates = get_templates()
    errors: dict[str, str] = {}

    # Validate inputs
    first_name = first_name.strip()
    last_name = last_name.strip()
    display_name = display_name.strip() if display_name else None

    if not first_name:
        errors["first_name"] = "First name is required"
    if not last_name:
        errors["last_name"] = "Last name is required"

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="profile/edit.html",
            context={
                "user": current_user,
                "first_name": first_name,
                "last_name": last_name,
                "display_name": display_name,
                "errors": errors,
            },
        )

    # Update user
    current_user.first_name = first_name
    current_user.last_name = last_name
    current_user.display_name = display_name if display_name else None

    await db.flush()

    return RedirectResponse(url="/profile", status_code=303)


@router.get("/profile/settings", response_class=HTMLResponse)
async def profile_settings_form(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Profile settings page."""
    templates = get_templates()
    return templates.TemplateResponse(
        request=request,
        name="profile/settings.html",
        context={"user": current_user},
    )


@router.post("/profile/settings", response_class=HTMLResponse)
async def profile_settings_submit(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    action: Annotated[str, Form()],
    current_password: Annotated[str | None, Form()] = None,
    new_password: Annotated[str | None, Form()] = None,
    confirm_password: Annotated[str | None, Form()] = None,
    timezone: Annotated[str | None, Form()] = None,
    language: Annotated[str | None, Form()] = None,
    theme: Annotated[str | None, Form()] = None,
) -> Response:
    """Process profile settings update."""
    templates = get_templates()

    if action == "change_password":
        return await _handle_password_change(
            request=request,
            db=db,
            user=current_user,
            current_password=current_password,
            new_password=new_password,
            confirm_password=confirm_password,
            templates=templates,
        )
    elif action == "update_preferences":
        return await _handle_preferences_update(
            request=request,
            db=db,
            user=current_user,
            timezone=timezone,
            language=language,
            theme=theme,
            templates=templates,
        )

    # Unknown action - redirect to settings
    return RedirectResponse(url="/profile/settings", status_code=303)


async def _handle_password_change(
    request: Request,
    db: AsyncSession,
    user: User,
    current_password: str | None,
    new_password: str | None,
    confirm_password: str | None,
    templates: Jinja2Templates,
) -> Response:
    """Handle password change form submission."""
    errors: dict[str, str] = {}

    # Validate current password
    if not current_password:
        errors["current_password"] = "Current password is required"
    elif not verify_password(current_password, user.hashed_password):
        errors["current_password"] = "Current password is incorrect"

    # Validate new password
    if not new_password:
        errors["new_password"] = "New password is required"
    elif len(new_password) < 8:
        errors["new_password"] = "Password must be at least 8 characters"

    # Validate confirm password
    if not confirm_password:
        errors["confirm_password"] = "Please confirm your new password"
    elif new_password and confirm_password != new_password:
        errors["confirm_password"] = "Passwords do not match"

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="profile/settings.html",
            context={
                "user": user,
                "errors": errors,
                "password_error": "Please correct the errors below",
            },
        )

    # Update password (new_password is guaranteed to be non-None here due to validation)
    assert new_password is not None
    user.hashed_password = hash_password(new_password)
    await db.flush()

    return templates.TemplateResponse(
        request=request,
        name="profile/settings.html",
        context={
            "user": user,
            "password_success": "Your password has been updated successfully",
        },
    )


async def _handle_preferences_update(
    request: Request,
    db: AsyncSession,
    user: User,
    timezone: str | None,
    language: str | None,
    theme: str | None,
    templates: Jinja2Templates,
) -> Response:
    """Handle preferences update form submission."""
    # Valid values
    valid_timezones = {
        "UTC",
        "America/New_York",
        "America/Chicago",
        "America/Denver",
        "America/Los_Angeles",
        "Europe/London",
        "Europe/Paris",
        "Europe/Berlin",
        "Asia/Tokyo",
        "Asia/Shanghai",
        "Australia/Sydney",
    }
    valid_languages = {"en", "es", "fr", "de", "ja", "zh"}
    valid_themes = {"system", "light", "dark"}

    # Update with validation
    if timezone and timezone in valid_timezones:
        user.timezone = timezone
    if language and language in valid_languages:
        user.language = language
    if theme and theme in valid_themes:
        user.theme = theme

    await db.flush()

    return templates.TemplateResponse(
        request=request,
        name="profile/settings.html",
        context={
            "user": user,
            "preferences_success": "Your preferences have been saved",
        },
    )
