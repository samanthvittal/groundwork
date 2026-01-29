"""Project management view routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from groundwork.auth.dependencies import CurrentUser
from groundwork.auth.models import User
from groundwork.core.database import get_db
from groundwork.core.templates import get_templates
from groundwork.projects.models import (
    Project,
    ProjectMember,
    ProjectRole,
    ProjectStatus,
    ProjectVisibility,
)
from groundwork.issues.services import IssueService, IssueTypeService, StatusService
from groundwork.projects.services import ProjectService

router = APIRouter()

# Key validation pattern - uppercase letters and numbers, starting with letter
KEY_PATTERN_DESCRIPTION = "2-10 uppercase letters/numbers, starting with a letter"


@router.get("/projects", response_class=HTMLResponse)
async def projects_list(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    search: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    success: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
) -> Response:
    """List projects."""
    templates = get_templates()

    # Build query - non-admins see only their projects
    if current_user.is_admin:
        # Admin query
        query = select(Project).options(selectinload(Project.members))
        if status:
            try:
                status_enum = ProjectStatus(status)
                query = query.where(Project.status == status_enum)
            except ValueError:
                pass
        else:
            # Default: show active projects
            query = query.where(Project.status == ProjectStatus.ACTIVE)
    else:
        # Non-admin: show projects they are owner or member of
        owned_query = select(Project.id).where(Project.owner_id == current_user.id)
        member_query = select(ProjectMember.project_id).where(
            ProjectMember.user_id == current_user.id
        )
        combined_ids = owned_query.union(member_query)
        query = (
            select(Project)
            .options(selectinload(Project.members))
            .where(Project.id.in_(combined_ids))
            .where(Project.status == ProjectStatus.ACTIVE)
        )

    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.where(
            Project.name.ilike(search_term) | Project.key.ilike(search_term)
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Pagination
    per_page = 20
    offset = (page - 1) * per_page
    query = query.order_by(Project.created_at.desc()).offset(offset).limit(per_page)

    result = await db.execute(query)
    projects = list(result.scalars().all())

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

    return templates.TemplateResponse(
        request=request,
        name="projects/list.html",
        context={
            "current_user": current_user,
            "projects": projects,
            "pagination": pagination,
            "search": search,
            "selected_status": status,
            "success": success,
            "error": error,
        },
    )


@router.get("/projects/create", response_class=HTMLResponse)
async def projects_create_form(
    request: Request,
    current_user: CurrentUser,
) -> Response:
    """Show create project form."""
    templates = get_templates()

    return templates.TemplateResponse(
        request=request,
        name="projects/create.html",
        context={
            "current_user": current_user,
            "visibilities": [v for v in ProjectVisibility],
            "errors": {},
            "key": "",
            "name": "",
            "description": "",
            "selected_visibility": "private",
        },
    )


@router.post("/projects/create", response_class=HTMLResponse)
async def projects_create_submit(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    key: Annotated[str, Form()],
    name: Annotated[str, Form()],
    description: Annotated[str | None, Form()] = None,
    visibility: Annotated[str, Form()] = "private",
) -> Response:
    """Create a new project."""
    templates = get_templates()
    errors: dict[str, str] = {}

    # Clean inputs
    key = key.strip().upper()
    name = name.strip()
    description = description.strip() if description else None

    # Validate key
    if not key:
        errors["key"] = "Project key is required"
    elif len(key) < 2 or len(key) > 10:
        errors["key"] = "Key must be 2-10 characters"
    elif not key[0].isalpha():
        errors["key"] = "Key must start with a letter"
    elif not key.isalnum():
        errors["key"] = "Key must contain only letters and numbers"
    else:
        # Check if key already exists
        existing = await db.execute(select(Project).where(Project.key == key))
        if existing.scalar_one_or_none():
            errors["key"] = "A project with this key already exists"

    # Validate name
    if not name:
        errors["name"] = "Project name is required"
    elif len(name) > 200:
        errors["name"] = "Name must be 200 characters or less"

    # Validate visibility
    try:
        visibility_enum = ProjectVisibility(visibility)
    except ValueError:
        errors["visibility"] = "Invalid visibility option"
        visibility_enum = ProjectVisibility.PRIVATE

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="projects/create.html",
            context={
                "current_user": current_user,
                "visibilities": [v for v in ProjectVisibility],
                "key": key,
                "name": name,
                "description": description,
                "selected_visibility": visibility,
                "errors": errors,
            },
        )

    # Create project
    service = ProjectService(db)
    project = await service.create_project(
        key=key,
        name=name,
        owner_id=current_user.id,
        description=description,
        visibility=visibility_enum,
    )

    if project is None:
        errors["key"] = "A project with this key already exists"
        return templates.TemplateResponse(
            request=request,
            name="projects/create.html",
            context={
                "current_user": current_user,
                "visibilities": [v for v in ProjectVisibility],
                "key": key,
                "name": name,
                "description": description,
                "selected_visibility": visibility,
                "errors": errors,
            },
        )

    return RedirectResponse(
        url=f"/projects/{project.id}?success=Project+created+successfully",
        status_code=303,
    )


@router.get("/projects/{project_id}", response_class=HTMLResponse)
async def projects_detail(
    request: Request,
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    success: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
) -> Response:
    """Show project detail page with inline issues."""
    templates = get_templates()
    service = ProjectService(db)

    try:
        project_uuid = UUID(project_id)
    except ValueError:
        return RedirectResponse(
            url="/projects?error=Invalid+project+ID", status_code=303
        )

    project = await service.get_project(project_uuid)

    if not project:
        return RedirectResponse(
            url="/projects?error=Project+not+found", status_code=303
        )

    # Check access
    if not current_user.is_admin:
        can_access = await service.user_can_access(project_uuid, current_user.id)
        if not can_access:
            return RedirectResponse(
                url="/projects?error=You+don't+have+access+to+this+project",
                status_code=303,
            )

    # Check permissions
    can_edit = current_user.is_admin or await service.user_can_edit(
        project_uuid, current_user.id
    )
    can_admin = current_user.is_admin or await service.user_can_admin(
        project_uuid, current_user.id
    )
    is_owner = current_user.is_admin or await service.user_is_owner(
        project_uuid, current_user.id
    )

    # Get members with user details
    members = await service.list_project_members(project_uuid)

    # Get issues for inline display
    issue_service = IssueService(db)
    per_page = 20
    issues = await issue_service.list_issues(
        project_id=project_uuid,
        parent_id=None,
        skip=(page - 1) * per_page,
        limit=per_page,
    )
    total_issues = await issue_service.count_issues(project_uuid)

    # Can create issues (any project member)
    can_create_issue = current_user.is_admin
    if not can_create_issue:
        member = await service.get_member(project_uuid, current_user.id)
        can_create_issue = member is not None

    # Build pagination
    issues_pagination = None
    if total_issues > 0:
        start = (page - 1) * per_page + 1
        end = min(page * per_page, total_issues)
        issues_pagination = {
            "page": page,
            "total": total_issues,
            "start": start,
            "end": end,
            "has_prev": page > 1,
            "has_next": end < total_issues,
        }

    return templates.TemplateResponse(
        request=request,
        name="projects/detail.html",
        context={
            "current_user": current_user,
            "project": project,
            "members": members,
            "issues": issues,
            "issues_pagination": issues_pagination,
            "can_edit": can_edit,
            "can_admin": can_admin,
            "can_create_issue": can_create_issue,
            "is_owner": is_owner,
            "success": success,
            "error": error,
        },
    )


@router.get("/projects/{project_id}/edit", response_class=HTMLResponse)
async def projects_edit_form(
    request: Request,
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> Response:
    """Show edit project form."""
    templates = get_templates()
    service = ProjectService(db)

    try:
        project_uuid = UUID(project_id)
    except ValueError:
        return RedirectResponse(
            url="/projects?error=Invalid+project+ID", status_code=303
        )

    # Check admin access
    if not current_user.is_admin:
        can_admin = await service.user_can_admin(project_uuid, current_user.id)
        if not can_admin:
            return RedirectResponse(
                url=f"/projects/{project_id}?error=You+don't+have+permission+to+edit+this+project",
                status_code=303,
            )

    project = await service.get_project(project_uuid)

    if not project:
        return RedirectResponse(
            url="/projects?error=Project+not+found", status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="projects/edit.html",
        context={
            "current_user": current_user,
            "project": project,
            "visibilities": [v for v in ProjectVisibility],
            "statuses": [s for s in ProjectStatus if s != ProjectStatus.DELETED],
            "errors": {},
        },
    )


@router.post("/projects/{project_id}/edit", response_class=HTMLResponse)
async def projects_edit_submit(
    request: Request,
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    name: Annotated[str, Form()],
    description: Annotated[str | None, Form()] = None,
    visibility: Annotated[str, Form()] = "private",
    status: Annotated[str, Form()] = "active",
) -> Response:
    """Update project."""
    templates = get_templates()
    service = ProjectService(db)

    try:
        project_uuid = UUID(project_id)
    except ValueError:
        return RedirectResponse(
            url="/projects?error=Invalid+project+ID", status_code=303
        )

    # Check admin access
    if not current_user.is_admin:
        can_admin = await service.user_can_admin(project_uuid, current_user.id)
        if not can_admin:
            return RedirectResponse(
                url=f"/projects/{project_id}?error=You+don't+have+permission+to+edit+this+project",
                status_code=303,
            )

    project = await service.get_project(project_uuid)
    if not project:
        return RedirectResponse(
            url="/projects?error=Project+not+found", status_code=303
        )

    errors: dict[str, str] = {}

    # Clean inputs
    name = name.strip()
    description = description.strip() if description else None

    # Validate name
    if not name:
        errors["name"] = "Project name is required"
    elif len(name) > 200:
        errors["name"] = "Name must be 200 characters or less"

    # Validate visibility
    try:
        visibility_enum = ProjectVisibility(visibility)
    except ValueError:
        errors["visibility"] = "Invalid visibility option"
        visibility_enum = project.visibility

    # Validate status
    try:
        status_enum = ProjectStatus(status)
    except ValueError:
        errors["status"] = "Invalid status option"
        status_enum = project.status

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="projects/edit.html",
            context={
                "current_user": current_user,
                "project": project,
                "visibilities": [v for v in ProjectVisibility],
                "statuses": [s for s in ProjectStatus if s != ProjectStatus.DELETED],
                "name": name,
                "description": description,
                "selected_visibility": visibility,
                "selected_status": status,
                "errors": errors,
            },
        )

    # Update project
    project = await service.update_project(
        project_id=project_uuid,
        name=name,
        description=description,
        visibility=visibility_enum,
        status=status_enum,
    )

    return RedirectResponse(
        url=f"/projects/{project_id}?success=Project+updated+successfully",
        status_code=303,
    )


@router.post("/projects/{project_id}/delete", response_class=HTMLResponse)
async def projects_delete(
    request: Request,
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> Response:
    """Delete a project."""
    service = ProjectService(db)

    try:
        project_uuid = UUID(project_id)
    except ValueError:
        return RedirectResponse(
            url="/projects?error=Invalid+project+ID", status_code=303
        )

    # Only owner can delete
    if not current_user.is_admin:
        is_owner = await service.user_is_owner(project_uuid, current_user.id)
        if not is_owner:
            return RedirectResponse(
                url=f"/projects/{project_id}?error=Only+the+project+owner+can+delete+the+project",
                status_code=303,
            )

    result = await service.delete_project(project_uuid)

    if not result:
        return RedirectResponse(
            url="/projects?error=Project+not+found", status_code=303
        )

    return RedirectResponse(
        url="/projects?success=Project+deleted+successfully", status_code=303
    )


# Member management views


@router.get("/projects/{project_id}/members", response_class=HTMLResponse)
async def projects_members(
    request: Request,
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    success: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
) -> Response:
    """Show project members management page."""
    templates = get_templates()
    service = ProjectService(db)

    try:
        project_uuid = UUID(project_id)
    except ValueError:
        return RedirectResponse(
            url="/projects?error=Invalid+project+ID", status_code=303
        )

    project = await service.get_project(project_uuid)

    if not project:
        return RedirectResponse(
            url="/projects?error=Project+not+found", status_code=303
        )

    # Check admin access
    can_admin = current_user.is_admin or await service.user_can_admin(
        project_uuid, current_user.id
    )

    if not can_admin:
        return RedirectResponse(
            url=f"/projects/{project_id}?error=You+don't+have+permission+to+manage+members",
            status_code=303,
        )

    members = await service.list_project_members(project_uuid)

    # Get available users for adding
    users_result = await db.execute(
        select(User).where(User.is_active.is_(True)).order_by(User.email)
    )
    all_users = list(users_result.scalars().all())
    member_user_ids = {m.user_id for m in members}
    available_users = [u for u in all_users if u.id not in member_user_ids]

    return templates.TemplateResponse(
        request=request,
        name="projects/members.html",
        context={
            "current_user": current_user,
            "project": project,
            "members": members,
            "available_users": available_users,
            "roles": [r for r in ProjectRole],
            "success": success,
            "error": error,
        },
    )


@router.post("/projects/{project_id}/members/add", response_class=HTMLResponse)
async def projects_members_add(
    request: Request,
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    user_id: Annotated[str, Form()],
    role: Annotated[str, Form()],
) -> Response:
    """Add a member to the project."""
    service = ProjectService(db)

    try:
        project_uuid = UUID(project_id)
        user_uuid = UUID(user_id)
    except ValueError:
        return RedirectResponse(
            url=f"/projects/{project_id}/members?error=Invalid+ID", status_code=303
        )

    # Check admin access
    if not current_user.is_admin:
        can_admin = await service.user_can_admin(project_uuid, current_user.id)
        if not can_admin:
            return RedirectResponse(
                url=f"/projects/{project_id}/members?error=Permission+denied",
                status_code=303,
            )

    try:
        role_enum = ProjectRole(role)
    except ValueError:
        return RedirectResponse(
            url=f"/projects/{project_id}/members?error=Invalid+role", status_code=303
        )

    member = await service.add_member(project_uuid, user_uuid, role_enum)

    if member is None:
        return RedirectResponse(
            url=f"/projects/{project_id}/members?error=User+is+already+a+member",
            status_code=303,
        )

    return RedirectResponse(
        url=f"/projects/{project_id}/members?success=Member+added+successfully",
        status_code=303,
    )


@router.post(
    "/projects/{project_id}/members/{user_id}/update", response_class=HTMLResponse
)
async def projects_members_update(
    request: Request,
    project_id: str,
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    role: Annotated[str, Form()],
) -> Response:
    """Update a member's role."""
    service = ProjectService(db)

    try:
        project_uuid = UUID(project_id)
        user_uuid = UUID(user_id)
    except ValueError:
        return RedirectResponse(
            url=f"/projects/{project_id}/members?error=Invalid+ID", status_code=303
        )

    # Check admin access
    if not current_user.is_admin:
        can_admin = await service.user_can_admin(project_uuid, current_user.id)
        if not can_admin:
            return RedirectResponse(
                url=f"/projects/{project_id}/members?error=Permission+denied",
                status_code=303,
            )

    try:
        role_enum = ProjectRole(role)
    except ValueError:
        return RedirectResponse(
            url=f"/projects/{project_id}/members?error=Invalid+role", status_code=303
        )

    member = await service.update_member_role(project_uuid, user_uuid, role_enum)

    if member is None:
        return RedirectResponse(
            url=f"/projects/{project_id}/members?error=Member+not+found",
            status_code=303,
        )

    return RedirectResponse(
        url=f"/projects/{project_id}/members?success=Role+updated+successfully",
        status_code=303,
    )


@router.post(
    "/projects/{project_id}/members/{user_id}/remove", response_class=HTMLResponse
)
async def projects_members_remove(
    request: Request,
    project_id: str,
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> Response:
    """Remove a member from the project."""
    service = ProjectService(db)

    try:
        project_uuid = UUID(project_id)
        user_uuid = UUID(user_id)
    except ValueError:
        return RedirectResponse(
            url=f"/projects/{project_id}/members?error=Invalid+ID", status_code=303
        )

    # Check if user is removing themselves (always allowed)
    is_self = user_uuid == current_user.id

    if not is_self and not current_user.is_admin:
        can_admin = await service.user_can_admin(project_uuid, current_user.id)
        if not can_admin:
            return RedirectResponse(
                url=f"/projects/{project_id}/members?error=Permission+denied",
                status_code=303,
            )

    result = await service.remove_member(project_uuid, user_uuid)

    if not result:
        return RedirectResponse(
            url=f"/projects/{project_id}/members?error=Member+not+found",
            status_code=303,
        )

    # If user removed themselves, redirect to projects list
    if is_self:
        return RedirectResponse(
            url="/projects?success=You+have+left+the+project", status_code=303
        )

    return RedirectResponse(
        url=f"/projects/{project_id}/members?success=Member+removed+successfully",
        status_code=303,
    )
