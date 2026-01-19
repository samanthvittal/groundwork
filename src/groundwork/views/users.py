"""User management view routes."""

import re
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from groundwork.auth.dependencies import CurrentUser, require_permission
from groundwork.auth.models import Role, User
from groundwork.auth.utils import hash_password
from groundwork.core.database import get_db
from groundwork.core.templates import get_templates

router = APIRouter()

# Email regex pattern
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


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


@router.get("/users", response_class=HTMLResponse)
async def users_list(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(check_users_read)],
    search: Annotated[str | None, Query()] = None,
    role: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
) -> Response:
    """List all users."""
    templates = get_templates()

    # Build query
    query = select(User).options(selectinload(User.role))

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                User.email.ilike(search_term),
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
            )
        )

    if role:
        try:
            role_uuid = UUID(role)
            query = query.where(User.role_id == role_uuid)
        except ValueError:
            pass  # Ignore invalid UUID

    if status:
        if status == "active":
            query = query.where(User.is_active.is_(True))
        elif status == "inactive":
            query = query.where(User.is_active.is_(False))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Pagination
    per_page = 20
    offset = (page - 1) * per_page
    query = query.order_by(User.created_at.desc()).offset(offset).limit(per_page)

    result = await db.execute(query)
    users = list(result.scalars().all())

    # Get all roles for filter dropdown
    roles_result = await db.execute(select(Role).order_by(Role.name))
    roles = list(roles_result.scalars().all())

    # Build pagination info
    pagination = None
    if total > 0:
        start = offset + 1
        end = min(offset + per_page, total)
        pagination = {
            "page": page,
            "total": total,
            "start": start,
            "end": end,
            "has_prev": page > 1,
            "has_next": end < total,
        }

    # Check user permissions
    can_create = current_user.role.has_permission("users:create")
    can_update = current_user.role.has_permission("users:update")

    return templates.TemplateResponse(
        request=request,
        name="users/list.html",
        context={
            "user": current_user,
            "users": users,
            "roles": roles,
            "pagination": pagination,
            "search": search,
            "selected_role": role,
            "selected_status": status,
            "can_create": can_create,
            "can_update": can_update,
        },
    )


@router.get("/users/create", response_class=HTMLResponse)
async def users_create_form(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(check_users_create)],
) -> Response:
    """Show create user form."""
    templates = get_templates()

    # Get all roles
    roles_result = await db.execute(select(Role).order_by(Role.name))
    roles = list(roles_result.scalars().all())

    return templates.TemplateResponse(
        request=request,
        name="users/create.html",
        context={
            "user": current_user,
            "roles": roles,
        },
    )


@router.post("/users/create", response_class=HTMLResponse)
async def users_create_submit(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(check_users_create)],
    email: Annotated[str, Form()],
    first_name: Annotated[str, Form()],
    last_name: Annotated[str, Form()],
    password: Annotated[str, Form()],
    confirm_password: Annotated[str, Form()],
    role_id: Annotated[str, Form()],
    is_active: Annotated[str | None, Form()] = None,
) -> Response:
    """Create a new user."""
    templates = get_templates()
    errors: dict[str, str] = {}

    # Clean inputs
    email = email.strip().lower()
    first_name = first_name.strip()
    last_name = last_name.strip()

    # Validate email
    if not email:
        errors["email"] = "Email is required"
    elif not EMAIL_PATTERN.match(email):
        errors["email"] = "Invalid email format"
    else:
        # Check if email already exists
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            errors["email"] = "A user with this email already exists"

    # Validate names
    if not first_name:
        errors["first_name"] = "First name is required"
    if not last_name:
        errors["last_name"] = "Last name is required"

    # Validate password
    if not password:
        errors["password"] = "Password is required"
    elif len(password) < 8:
        errors["password"] = "Password must be at least 8 characters"

    # Validate confirm password
    if not confirm_password:
        errors["confirm_password"] = "Please confirm the password"
    elif password and confirm_password != password:
        errors["confirm_password"] = "Passwords do not match"

    # Validate role
    role_uuid = None
    if not role_id:
        errors["role_id"] = "Role is required"
    else:
        try:
            role_uuid = UUID(role_id)
            role_result = await db.execute(select(Role).where(Role.id == role_uuid))
            if not role_result.scalar_one_or_none():
                errors["role_id"] = "Invalid role selected"
        except ValueError:
            errors["role_id"] = "Invalid role selected"

    # Get roles for re-rendering form
    roles_result = await db.execute(select(Role).order_by(Role.name))
    roles = list(roles_result.scalars().all())

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="users/create.html",
            context={
                "user": current_user,
                "roles": roles,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "selected_role_id": role_id,
                "is_active": is_active == "true",
                "errors": errors,
            },
        )

    # Create user
    new_user = User(
        email=email,
        hashed_password=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        role_id=role_uuid,
        is_active=is_active == "true",
    )
    db.add(new_user)
    await db.flush()

    return RedirectResponse(
        url=f"/users/{new_user.id}?success=User+created+successfully",
        status_code=303,
    )


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def users_detail(
    request: Request,
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(check_users_read)],
    success: Annotated[str | None, Query()] = None,
) -> Response:
    """Show user detail page."""
    templates = get_templates()

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        return RedirectResponse(url="/users?error=Invalid+user+ID", status_code=303)

    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_uuid)
    )
    target_user = result.scalar_one_or_none()

    if not target_user:
        return RedirectResponse(url="/users?error=User+not+found", status_code=303)

    # Check permissions
    can_update = current_user.role.has_permission("users:update")
    can_delete = current_user.role.has_permission("users:delete")

    return templates.TemplateResponse(
        request=request,
        name="users/detail.html",
        context={
            "user": current_user,
            "current_user": current_user,
            "target_user": target_user,
            "can_update": can_update,
            "can_delete": can_delete,
            "success": success,
            "activity_log": None,  # Placeholder for future activity log feature
        },
    )


@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def users_edit_form(
    request: Request,
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(check_users_update)],
) -> Response:
    """Show edit user form."""
    templates = get_templates()

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        return RedirectResponse(url="/users?error=Invalid+user+ID", status_code=303)

    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_uuid)
    )
    target_user = result.scalar_one_or_none()

    if not target_user:
        return RedirectResponse(url="/users?error=User+not+found", status_code=303)

    # Get all roles
    roles_result = await db.execute(select(Role).order_by(Role.name))
    roles = list(roles_result.scalars().all())

    return templates.TemplateResponse(
        request=request,
        name="users/edit.html",
        context={
            "user": current_user,
            "current_user": current_user,
            "target_user": target_user,
            "roles": roles,
        },
    )


@router.post("/users/{user_id}/edit", response_class=HTMLResponse)
async def users_edit_submit(
    request: Request,
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(check_users_update)],
    action: Annotated[str | None, Form()] = None,
    first_name: Annotated[str | None, Form()] = None,
    last_name: Annotated[str | None, Form()] = None,
    display_name: Annotated[str | None, Form()] = None,
    role_id: Annotated[str | None, Form()] = None,
    is_active: Annotated[str | None, Form()] = None,
    new_password: Annotated[str | None, Form()] = None,
    confirm_new_password: Annotated[str | None, Form()] = None,
) -> Response:
    """Update user or reset password."""
    templates = get_templates()

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        return RedirectResponse(url="/users?error=Invalid+user+ID", status_code=303)

    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_uuid)
    )
    target_user = result.scalar_one_or_none()

    if not target_user:
        return RedirectResponse(url="/users?error=User+not+found", status_code=303)

    # Get all roles for re-rendering form
    roles_result = await db.execute(select(Role).order_by(Role.name))
    roles = list(roles_result.scalars().all())

    # Handle password reset
    if action == "reset_password":
        return await _handle_password_reset(
            request=request,
            db=db,
            current_user=current_user,
            target_user=target_user,
            roles=roles,
            new_password=new_password,
            confirm_new_password=confirm_new_password,
            templates=templates,
        )

    # Handle user update
    errors: dict[str, str] = {}

    # Clean inputs
    first_name = first_name.strip() if first_name else ""
    last_name = last_name.strip() if last_name else ""
    display_name = display_name.strip() if display_name else None

    # Validate names
    if not first_name:
        errors["first_name"] = "First name is required"
    if not last_name:
        errors["last_name"] = "Last name is required"

    # Validate role
    role_uuid = None
    if not role_id:
        errors["role_id"] = "Role is required"
    else:
        try:
            role_uuid = UUID(role_id)
            role_result = await db.execute(select(Role).where(Role.id == role_uuid))
            if not role_result.scalar_one_or_none():
                errors["role_id"] = "Invalid role selected"
        except ValueError:
            errors["role_id"] = "Invalid role selected"

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="users/edit.html",
            context={
                "user": current_user,
                "current_user": current_user,
                "target_user": target_user,
                "roles": roles,
                "first_name": first_name,
                "last_name": last_name,
                "display_name": display_name,
                "selected_role_id": role_id,
                "is_active": is_active == "true",
                "errors": errors,
            },
        )

    # Update user (role_uuid is guaranteed non-None due to validation above)
    assert role_uuid is not None
    target_user.first_name = first_name
    target_user.last_name = last_name
    target_user.display_name = display_name if display_name else None
    target_user.role_id = role_uuid

    # Only update is_active if not editing own account
    if target_user.id != current_user.id:
        target_user.is_active = is_active == "true"

    await db.flush()

    return RedirectResponse(
        url=f"/users/{target_user.id}?success=User+updated+successfully",
        status_code=303,
    )


async def _handle_password_reset(
    request: Request,
    db: AsyncSession,
    current_user: User,
    target_user: User,
    roles: list[Role],
    new_password: str | None,
    confirm_new_password: str | None,
    templates: Jinja2Templates,
) -> Response:
    """Handle password reset form submission."""
    password_errors: dict[str, str] = {}

    # Validate new password
    if not new_password:
        password_errors["new_password"] = "New password is required"
    elif len(new_password) < 8:
        password_errors["new_password"] = "Password must be at least 8 characters"

    # Validate confirm password
    if not confirm_new_password:
        password_errors["confirm_password"] = "Please confirm the password"
    elif new_password and confirm_new_password != new_password:
        password_errors["confirm_password"] = "Passwords do not match"

    if password_errors:
        return templates.TemplateResponse(
            request=request,
            name="users/edit.html",
            context={
                "user": current_user,
                "current_user": current_user,
                "target_user": target_user,
                "roles": roles,
                "password_errors": password_errors,
                "password_error": "Please correct the errors below",
            },
        )

    # Update password (new_password is guaranteed non-None due to validation above)
    assert new_password is not None
    target_user.hashed_password = hash_password(new_password)
    await db.flush()

    return templates.TemplateResponse(
        request=request,
        name="users/edit.html",
        context={
            "user": current_user,
            "current_user": current_user,
            "target_user": target_user,
            "roles": roles,
            "password_success": "Password has been reset successfully",
        },
    )


@router.post("/users/{user_id}/delete", response_class=HTMLResponse)
async def users_delete(
    request: Request,
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(check_users_delete)],
) -> Response:
    """Delete a user."""
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        return RedirectResponse(url="/users?error=Invalid+user+ID", status_code=303)

    result = await db.execute(select(User).where(User.id == user_uuid))
    target_user = result.scalar_one_or_none()

    if not target_user:
        return RedirectResponse(url="/users?error=User+not+found", status_code=303)

    # Prevent self-deletion
    if target_user.id == current_user.id:
        return RedirectResponse(
            url=f"/users/{user_id}?error=You+cannot+delete+your+own+account",
            status_code=303,
        )

    # Delete user
    await db.delete(target_user)
    await db.flush()

    return RedirectResponse(
        url="/users?success=User+deleted+successfully", status_code=303
    )
