"""Role management view routes."""

import contextlib
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from groundwork.auth.dependencies import CurrentUser, require_permission
from groundwork.auth.models import Role, User
from groundwork.core.database import get_db
from groundwork.core.templates import get_templates
from groundwork.roles.services import RoleService

router = APIRouter()


# Permission check functions that wrap require_permission with CurrentUser dependency
def check_roles_read(current_user: CurrentUser) -> User:
    """Check roles:read permission."""
    return require_permission("roles:read")(current_user)


def check_roles_create(current_user: CurrentUser) -> User:
    """Check roles:create permission."""
    return require_permission("roles:create")(current_user)


def check_roles_update(current_user: CurrentUser) -> User:
    """Check roles:update permission."""
    return require_permission("roles:update")(current_user)


def check_roles_delete(current_user: CurrentUser) -> User:
    """Check roles:delete permission."""
    return require_permission("roles:delete")(current_user)


@router.get("/roles", response_class=HTMLResponse)
async def roles_list(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(check_roles_read)],
    success: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
) -> Response:
    """List all roles."""
    templates = get_templates()

    # Get roles with permissions and users loaded
    result = await db.execute(
        select(Role)
        .options(selectinload(Role.permissions), selectinload(Role.users))
        .order_by(Role.name)
    )
    roles = list(result.scalars().all())

    # Check user permissions
    can_create = current_user.role.has_permission("roles:create")
    can_update = current_user.role.has_permission("roles:update")
    can_delete = current_user.role.has_permission("roles:delete")

    return templates.TemplateResponse(
        request=request,
        name="roles/list.html",
        context={
            "user": current_user,
            "current_user": current_user,
            "roles": roles,
            "can_create": can_create,
            "can_update": can_update,
            "can_delete": can_delete,
            "success": success,
            "error": error,
        },
    )


@router.get("/roles/create", response_class=HTMLResponse)
async def roles_create_form(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(check_roles_create)],
) -> Response:
    """Show create role form."""
    templates = get_templates()
    service = RoleService(db)

    # Get all available permissions
    permissions = await service.list_permissions()

    return templates.TemplateResponse(
        request=request,
        name="roles/create.html",
        context={
            "user": current_user,
            "current_user": current_user,
            "permissions": permissions,
        },
    )


@router.post("/roles/create", response_class=HTMLResponse)
async def roles_create_submit(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(check_roles_create)],
    name: Annotated[str, Form()],
    description: Annotated[str, Form()],
    permissions: Annotated[list[str] | None, Form()] = None,
) -> Response:
    """Create a new role."""
    templates = get_templates()
    service = RoleService(db)
    errors: dict[str, str] = {}

    # Handle None permissions
    if permissions is None:
        permissions = []

    # Clean inputs
    name = name.strip()
    description = description.strip()

    # Validate name
    if not name:
        errors["name"] = "Name is required"
    elif len(name) > 100:
        errors["name"] = "Name must be 100 characters or less"

    # Validate description
    if not description:
        errors["description"] = "Description is required"
    elif len(description) > 500:
        errors["description"] = "Description must be 500 characters or less"

    # Get all available permissions for re-rendering form
    all_permissions = await service.list_permissions()

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="roles/create.html",
            context={
                "user": current_user,
                "current_user": current_user,
                "permissions": all_permissions,
                "name": name,
                "description": description,
                "selected_permissions": permissions,
                "errors": errors,
            },
        )

    # Convert permission strings to UUIDs
    permission_ids: list[UUID] = []
    for perm_id in permissions:
        with contextlib.suppress(ValueError):
            permission_ids.append(UUID(perm_id))

    # Create role
    role = await service.create_role(
        name=name,
        description=description,
        permission_ids=permission_ids,
    )

    if role is None:
        # Name already exists
        return templates.TemplateResponse(
            request=request,
            name="roles/create.html",
            context={
                "user": current_user,
                "current_user": current_user,
                "permissions": all_permissions,
                "name": name,
                "description": description,
                "selected_permissions": permissions,
                "errors": {"name": "A role with this name already exists"},
            },
        )

    return RedirectResponse(
        url=f"/roles/{role.id}?success=Role+created+successfully",
        status_code=303,
    )


@router.get("/roles/{role_id}", response_class=HTMLResponse)
async def roles_detail(
    request: Request,
    role_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(check_roles_read)],
    success: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
) -> Response:
    """Show role detail page."""
    templates = get_templates()

    try:
        role_uuid = UUID(role_id)
    except ValueError:
        return RedirectResponse(url="/roles?error=Invalid+role+ID", status_code=303)

    # Get role with permissions and users loaded
    result = await db.execute(
        select(Role)
        .options(selectinload(Role.permissions), selectinload(Role.users))
        .where(Role.id == role_uuid)
    )
    role = result.scalar_one_or_none()

    if not role:
        return RedirectResponse(url="/roles?error=Role+not+found", status_code=303)

    # Check permissions
    can_update = current_user.role.has_permission("roles:update")
    can_delete = current_user.role.has_permission("roles:delete")

    return templates.TemplateResponse(
        request=request,
        name="roles/detail.html",
        context={
            "user": current_user,
            "current_user": current_user,
            "role": role,
            "can_update": can_update,
            "can_delete": can_delete,
            "success": success,
            "error": error,
        },
    )


@router.get("/roles/{role_id}/edit", response_class=HTMLResponse)
async def roles_edit_form(
    request: Request,
    role_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(check_roles_update)],
) -> Response:
    """Show edit role form."""
    templates = get_templates()
    service = RoleService(db)

    try:
        role_uuid = UUID(role_id)
    except ValueError:
        return RedirectResponse(url="/roles?error=Invalid+role+ID", status_code=303)

    # Get role with permissions loaded
    role = await service.get_role(role_uuid)

    if not role:
        return RedirectResponse(url="/roles?error=Role+not+found", status_code=303)

    # Get all available permissions
    permissions = await service.list_permissions()

    return templates.TemplateResponse(
        request=request,
        name="roles/edit.html",
        context={
            "user": current_user,
            "current_user": current_user,
            "role": role,
            "permissions": permissions,
        },
    )


@router.post("/roles/{role_id}/edit", response_class=HTMLResponse)
async def roles_edit_submit(
    request: Request,
    role_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(check_roles_update)],
    name: Annotated[str, Form()],
    description: Annotated[str, Form()],
    permissions: Annotated[list[str] | None, Form()] = None,
) -> Response:
    """Update a role."""
    templates = get_templates()
    service = RoleService(db)
    errors: dict[str, str] = {}

    # Handle None permissions
    if permissions is None:
        permissions = []

    try:
        role_uuid = UUID(role_id)
    except ValueError:
        return RedirectResponse(url="/roles?error=Invalid+role+ID", status_code=303)

    # Get role with permissions loaded
    role = await service.get_role(role_uuid)

    if not role:
        return RedirectResponse(url="/roles?error=Role+not+found", status_code=303)

    # Clean inputs
    name = name.strip()
    description = description.strip()

    # Validate name
    if not name:
        errors["name"] = "Name is required"
    elif len(name) > 100:
        errors["name"] = "Name must be 100 characters or less"

    # Validate description
    if not description:
        errors["description"] = "Description is required"
    elif len(description) > 500:
        errors["description"] = "Description must be 500 characters or less"

    # Get all available permissions for re-rendering form
    all_permissions = await service.list_permissions()

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="roles/edit.html",
            context={
                "user": current_user,
                "current_user": current_user,
                "role": role,
                "permissions": all_permissions,
                "name": name,
                "description": description,
                "selected_permissions": permissions,
                "errors": errors,
            },
        )

    # Convert permission strings to UUIDs
    permission_ids: list[UUID] = []
    for perm_id in permissions:
        with contextlib.suppress(ValueError):
            permission_ids.append(UUID(perm_id))

    # For system roles, don't allow name change
    update_name = None if role.is_system else name

    # Update role
    result = await service.update_role(
        role_id=role_uuid,
        name=update_name,
        description=description,
        permission_ids=permission_ids,
    )

    if result == "duplicate":
        return templates.TemplateResponse(
            request=request,
            name="roles/edit.html",
            context={
                "user": current_user,
                "current_user": current_user,
                "role": role,
                "permissions": all_permissions,
                "name": name,
                "description": description,
                "selected_permissions": permissions,
                "errors": {"name": "A role with this name already exists"},
            },
        )

    return RedirectResponse(
        url=f"/roles/{role_id}?success=Role+updated+successfully",
        status_code=303,
    )


@router.post("/roles/{role_id}/delete", response_class=HTMLResponse)
async def roles_delete(
    request: Request,
    role_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(check_roles_delete)],
) -> Response:
    """Delete a role."""
    service = RoleService(db)

    try:
        role_uuid = UUID(role_id)
    except ValueError:
        return RedirectResponse(url="/roles?error=Invalid+role+ID", status_code=303)

    # Delete role
    result = await service.delete_role(role_uuid)

    if result is False:
        return RedirectResponse(url="/roles?error=Role+not+found", status_code=303)

    if result == "system":
        return RedirectResponse(
            url=f"/roles/{role_id}?error=System+roles+cannot+be+deleted",
            status_code=303,
        )

    return RedirectResponse(
        url="/roles?success=Role+deleted+successfully", status_code=303
    )
