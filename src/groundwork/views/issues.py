"""Issue management view routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.dependencies import CurrentUser
from groundwork.core.database import get_db
from groundwork.core.templates import get_templates
from groundwork.issues.models import Priority, StatusCategory
from groundwork.issues.services import (
    IssueService,
    IssueTypeService,
    LabelService,
    StatusService,
)
from groundwork.projects.services import ProjectService

router = APIRouter()


# =============================================================================
# Issues List (per project)
# =============================================================================


@router.get("/projects/{project_key}/issues", response_class=HTMLResponse)
async def issues_list(
    request: Request,
    project_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    status: Annotated[str | None, Query()] = None,
    type: Annotated[str | None, Query()] = None,
    assignee: Annotated[str | None, Query()] = None,
    priority: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    success: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
) -> Response:
    """List issues in a project."""
    templates = get_templates()
    project_service = ProjectService(db)

    # Get project
    project = await project_service.get_project_by_key(project_key.upper())
    if not project:
        return RedirectResponse(
            url="/projects?error=Project+not+found", status_code=303
        )

    # Check access
    if not current_user.is_admin:
        can_access = await project_service.user_can_access(project.id, current_user.id)
        if not can_access:
            return RedirectResponse(
                url="/projects?error=Access+denied", status_code=303
            )

    issue_service = IssueService(db)
    type_service = IssueTypeService(db)
    status_service = StatusService(db)

    # Parse filters
    status_id = None
    status_category = None
    if status:
        try:
            status_id = UUID(status)
        except ValueError:
            # Try as category
            try:
                status_category = StatusCategory(status)
            except ValueError:
                pass

    type_id = None
    if type:
        try:
            type_id = UUID(type)
        except ValueError:
            pass

    assignee_id = ...  # Sentinel for "any"
    if assignee == "me":
        assignee_id = current_user.id
    elif assignee == "unassigned":
        assignee_id = None  # Will filter for NULL assignee
    elif assignee:
        try:
            assignee_id = UUID(assignee)
        except ValueError:
            assignee_id = ...

    priority_filter = None
    if priority:
        try:
            priority_filter = Priority(priority)
        except ValueError:
            pass

    # Get issues
    per_page = 50
    issues = await issue_service.list_issues(
        project_id=project.id,
        status_category=status_category,
        status_id=status_id,
        type_id=type_id,
        assignee_id=assignee_id if assignee_id is not ... else None,
        priority=priority_filter,
        search=q,
        skip=(page - 1) * per_page,
        limit=per_page,
        parent_id=None,  # Only root issues
    )

    total = await issue_service.count_issues(project.id)

    # Get filter options
    issue_types = await type_service.list_issue_types(project.id)
    statuses = await status_service.list_statuses(project.id)

    # Group statuses by category for Kanban view
    statuses_by_category = {
        StatusCategory.TODO: [],
        StatusCategory.IN_PROGRESS: [],
        StatusCategory.DONE: [],
    }
    for s in statuses:
        statuses_by_category[s.category].append(s)

    # Check permissions
    can_create = current_user.is_admin
    if not can_create:
        member = await project_service.get_member(project.id, current_user.id)
        can_create = member is not None

    # Build pagination
    pagination = None
    if total > 0:
        start = (page - 1) * per_page + 1
        end = min(page * per_page, total)
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
        name="issues/list.html",
        context={
            "current_user": current_user,
            "project": project,
            "issues": issues,
            "issue_types": issue_types,
            "statuses": statuses,
            "statuses_by_category": statuses_by_category,
            "priorities": [p for p in Priority],
            "pagination": pagination,
            "filters": {
                "status": status,
                "type": type,
                "assignee": assignee,
                "priority": priority,
                "q": q,
            },
            "can_create": can_create,
            "success": success,
            "error": error,
        },
    )


# =============================================================================
# Issue Detail
# =============================================================================


@router.get("/issues/{issue_key}", response_class=HTMLResponse)
async def issue_detail(
    request: Request,
    issue_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    success: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
) -> Response:
    """Show issue detail page."""
    templates = get_templates()
    issue_service = IssueService(db)
    project_service = ProjectService(db)

    issue = await issue_service.get_issue_by_key(issue_key.upper())
    if not issue or issue.deleted_at:
        return RedirectResponse(
            url="/projects?error=Issue+not+found", status_code=303
        )

    # Check access via project
    if not current_user.is_admin:
        can_access = await project_service.user_can_access(
            issue.project_id, current_user.id
        )
        if not can_access:
            return RedirectResponse(
                url="/projects?error=Access+denied", status_code=303
            )

    # Get subtasks
    subtasks = await issue_service.list_subtasks(issue.id)

    # Get available types and statuses for editing
    type_service = IssueTypeService(db)
    status_service = StatusService(db)
    label_service = LabelService(db)

    issue_types = await type_service.list_issue_types(issue.project_id)
    statuses = await status_service.list_statuses(issue.project_id)
    labels = await label_service.list_labels(issue.project_id)

    # Check permissions
    can_edit = current_user.is_admin or await issue_service.user_can_edit(
        issue.id, current_user.id
    )
    can_delete = current_user.is_admin or await issue_service.user_can_delete(
        issue.id, current_user.id
    )

    return templates.TemplateResponse(
        request=request,
        name="issues/detail.html",
        context={
            "current_user": current_user,
            "issue": issue,
            "subtasks": subtasks,
            "issue_types": issue_types,
            "statuses": statuses,
            "labels": labels,
            "priorities": [p for p in Priority],
            "can_edit": can_edit,
            "can_delete": can_delete,
            "success": success,
            "error": error,
        },
    )


# =============================================================================
# Create Issue
# =============================================================================


@router.get("/projects/{project_key}/issues/create", response_class=HTMLResponse)
async def issues_create_form(
    request: Request,
    project_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    parent: Annotated[str | None, Query()] = None,
) -> Response:
    """Show create issue form."""
    templates = get_templates()
    project_service = ProjectService(db)

    project = await project_service.get_project_by_key(project_key.upper())
    if not project:
        return RedirectResponse(
            url="/projects?error=Project+not+found", status_code=303
        )

    # Check membership
    if not current_user.is_admin:
        member = await project_service.get_member(project.id, current_user.id)
        if not member:
            return RedirectResponse(
                url=f"/projects/{project_key}/issues?error=Permission+denied",
                status_code=303,
            )

    # Get available options
    type_service = IssueTypeService(db)
    status_service = StatusService(db)

    issue_types = await type_service.list_issue_types(project.id)
    statuses = await status_service.list_statuses(project.id)

    # Get members for assignee dropdown
    members = await project_service.list_project_members(project.id)

    # Get parent issue if creating subtask
    parent_issue = None
    if parent:
        issue_service = IssueService(db)
        parent_issue = await issue_service.get_issue_by_key(parent.upper())

    return templates.TemplateResponse(
        request=request,
        name="issues/create.html",
        context={
            "current_user": current_user,
            "project": project,
            "issue_types": issue_types,
            "statuses": statuses,
            "members": members,
            "priorities": [p for p in Priority],
            "parent_issue": parent_issue,
            "errors": {},
        },
    )


@router.post("/projects/{project_key}/issues/create", response_class=HTMLResponse)
async def issues_create_submit(
    request: Request,
    project_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    title: Annotated[str, Form()],
    type_id: Annotated[str, Form()],
    description: Annotated[str | None, Form()] = None,
    status_id: Annotated[str | None, Form()] = None,
    priority: Annotated[str, Form()] = "medium",
    assignee_id: Annotated[str | None, Form()] = None,
    parent_id: Annotated[str | None, Form()] = None,
) -> Response:
    """Create a new issue."""
    templates = get_templates()
    project_service = ProjectService(db)

    project = await project_service.get_project_by_key(project_key.upper())
    if not project:
        return RedirectResponse(
            url="/projects?error=Project+not+found", status_code=303
        )

    # Check membership
    if not current_user.is_admin:
        member = await project_service.get_member(project.id, current_user.id)
        if not member:
            return RedirectResponse(
                url=f"/projects/{project_key}/issues?error=Permission+denied",
                status_code=303,
            )

    errors: dict[str, str] = {}

    # Validate title
    title = title.strip()
    if not title:
        errors["title"] = "Title is required"
    elif len(title) > 500:
        errors["title"] = "Title must be 500 characters or less"

    # Validate type_id
    try:
        type_uuid = UUID(type_id)
    except ValueError:
        errors["type_id"] = "Invalid issue type"
        type_uuid = None

    # Parse optional UUIDs
    status_uuid = None
    if status_id:
        try:
            status_uuid = UUID(status_id)
        except ValueError:
            errors["status_id"] = "Invalid status"

    assignee_uuid = None
    if assignee_id:
        try:
            assignee_uuid = UUID(assignee_id)
        except ValueError:
            errors["assignee_id"] = "Invalid assignee"

    parent_uuid = None
    if parent_id:
        try:
            parent_uuid = UUID(parent_id)
        except ValueError:
            errors["parent_id"] = "Invalid parent issue"

    # Validate priority
    try:
        priority_enum = Priority(priority)
    except ValueError:
        errors["priority"] = "Invalid priority"
        priority_enum = Priority.MEDIUM

    if errors:
        # Re-render form with errors
        type_service = IssueTypeService(db)
        status_service = StatusService(db)
        issue_types = await type_service.list_issue_types(project.id)
        statuses = await status_service.list_statuses(project.id)
        members = await project_service.list_project_members(project.id)

        parent_issue = None
        if parent_id:
            issue_service = IssueService(db)
            parent_issue = await issue_service.get_issue(parent_uuid) if parent_uuid else None

        return templates.TemplateResponse(
            request=request,
            name="issues/create.html",
            context={
                "current_user": current_user,
                "project": project,
                "issue_types": issue_types,
                "statuses": statuses,
                "members": members,
                "priorities": [p for p in Priority],
                "parent_issue": parent_issue,
                "errors": errors,
                "title": title,
                "description": description,
                "selected_type": type_id,
                "selected_status": status_id,
                "selected_priority": priority,
                "selected_assignee": assignee_id,
            },
        )

    # Create issue
    issue_service = IssueService(db)
    issue = await issue_service.create_issue(
        project_id=project.id,
        title=title,
        type_id=type_uuid,
        reporter_id=current_user.id,
        description=description.strip() if description else None,
        status_id=status_uuid,
        priority=priority_enum,
        assignee_id=assignee_uuid,
        parent_id=parent_uuid,
    )

    return RedirectResponse(
        url=f"/issues/{issue.key}?success=Issue+created+successfully",
        status_code=303,
    )


# =============================================================================
# Edit Issue
# =============================================================================


@router.get("/issues/{issue_key}/edit", response_class=HTMLResponse)
async def issues_edit_form(
    request: Request,
    issue_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> Response:
    """Show edit issue form."""
    templates = get_templates()
    issue_service = IssueService(db)
    project_service = ProjectService(db)

    issue = await issue_service.get_issue_by_key(issue_key.upper())
    if not issue or issue.deleted_at:
        return RedirectResponse(
            url="/projects?error=Issue+not+found", status_code=303
        )

    # Check edit permission
    if not current_user.is_admin:
        can_edit = await issue_service.user_can_edit(issue.id, current_user.id)
        if not can_edit:
            return RedirectResponse(
                url=f"/issues/{issue_key}?error=Permission+denied",
                status_code=303,
            )

    # Get options
    type_service = IssueTypeService(db)
    status_service = StatusService(db)
    label_service = LabelService(db)

    issue_types = await type_service.list_issue_types(issue.project_id)
    statuses = await status_service.list_statuses(issue.project_id)
    labels = await label_service.list_labels(issue.project_id)
    members = await project_service.list_project_members(issue.project_id)

    return templates.TemplateResponse(
        request=request,
        name="issues/edit.html",
        context={
            "current_user": current_user,
            "issue": issue,
            "issue_types": issue_types,
            "statuses": statuses,
            "labels": labels,
            "members": members,
            "priorities": [p for p in Priority],
            "errors": {},
        },
    )


@router.post("/issues/{issue_key}/edit", response_class=HTMLResponse)
async def issues_edit_submit(
    request: Request,
    issue_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    title: Annotated[str, Form()],
    type_id: Annotated[str, Form()],
    status_id: Annotated[str, Form()],
    priority: Annotated[str, Form()],
    description: Annotated[str | None, Form()] = None,
    assignee_id: Annotated[str | None, Form()] = None,
) -> Response:
    """Update an issue."""
    templates = get_templates()
    issue_service = IssueService(db)
    project_service = ProjectService(db)

    issue = await issue_service.get_issue_by_key(issue_key.upper())
    if not issue or issue.deleted_at:
        return RedirectResponse(
            url="/projects?error=Issue+not+found", status_code=303
        )

    # Check edit permission
    if not current_user.is_admin:
        can_edit = await issue_service.user_can_edit(issue.id, current_user.id)
        if not can_edit:
            return RedirectResponse(
                url=f"/issues/{issue_key}?error=Permission+denied",
                status_code=303,
            )

    errors: dict[str, str] = {}

    # Validate
    title = title.strip()
    if not title:
        errors["title"] = "Title is required"
    elif len(title) > 500:
        errors["title"] = "Title must be 500 characters or less"

    try:
        type_uuid = UUID(type_id)
    except ValueError:
        errors["type_id"] = "Invalid issue type"
        type_uuid = issue.type_id

    try:
        status_uuid = UUID(status_id)
    except ValueError:
        errors["status_id"] = "Invalid status"
        status_uuid = issue.status_id

    try:
        priority_enum = Priority(priority)
    except ValueError:
        errors["priority"] = "Invalid priority"
        priority_enum = issue.priority

    assignee_uuid = ...  # Sentinel for "not provided"
    if assignee_id == "":
        assignee_uuid = None  # Explicitly unassign
    elif assignee_id:
        try:
            assignee_uuid = UUID(assignee_id)
        except ValueError:
            errors["assignee_id"] = "Invalid assignee"
            assignee_uuid = ...

    if errors:
        type_service = IssueTypeService(db)
        status_service = StatusService(db)
        label_service = LabelService(db)
        issue_types = await type_service.list_issue_types(issue.project_id)
        statuses = await status_service.list_statuses(issue.project_id)
        labels = await label_service.list_labels(issue.project_id)
        members = await project_service.list_project_members(issue.project_id)

        return templates.TemplateResponse(
            request=request,
            name="issues/edit.html",
            context={
                "current_user": current_user,
                "issue": issue,
                "issue_types": issue_types,
                "statuses": statuses,
                "labels": labels,
                "members": members,
                "priorities": [p for p in Priority],
                "errors": errors,
                "title": title,
                "description": description,
            },
        )

    # Update issue
    await issue_service.update_issue(
        issue_id=issue.id,
        title=title,
        description=description.strip() if description else None,
        type_id=type_uuid,
        status_id=status_uuid,
        priority=priority_enum,
        assignee_id=assignee_uuid,
    )

    return RedirectResponse(
        url=f"/issues/{issue_key}?success=Issue+updated+successfully",
        status_code=303,
    )


# =============================================================================
# Delete Issue
# =============================================================================


@router.post("/issues/{issue_key}/delete", response_class=HTMLResponse)
async def issues_delete(
    request: Request,
    issue_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> Response:
    """Delete an issue."""
    issue_service = IssueService(db)

    issue = await issue_service.get_issue_by_key(issue_key.upper())
    if not issue or issue.deleted_at:
        return RedirectResponse(
            url="/projects?error=Issue+not+found", status_code=303
        )

    project_key = issue.project.key

    # Check delete permission
    if not current_user.is_admin:
        can_delete = await issue_service.user_can_delete(issue.id, current_user.id)
        is_reporter = issue.reporter_id == current_user.id
        if not can_delete and not is_reporter:
            return RedirectResponse(
                url=f"/issues/{issue_key}?error=Permission+denied",
                status_code=303,
            )

    await issue_service.delete_issue(issue.id)

    return RedirectResponse(
        url=f"/projects/{project_key}/issues?success=Issue+deleted+successfully",
        status_code=303,
    )


# =============================================================================
# Quick Status Change (HTMX endpoint)
# =============================================================================


@router.post("/issues/{issue_key}/status", response_class=HTMLResponse)
async def issues_change_status(
    request: Request,
    issue_key: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    status_id: Annotated[str, Form()],
) -> Response:
    """Quick status change for an issue (HTMX endpoint)."""
    issue_service = IssueService(db)

    issue = await issue_service.get_issue_by_key(issue_key.upper())
    if not issue or issue.deleted_at:
        return Response(status_code=404)

    # Check edit permission
    if not current_user.is_admin:
        can_edit = await issue_service.user_can_edit(issue.id, current_user.id)
        if not can_edit:
            return Response(status_code=403)

    try:
        status_uuid = UUID(status_id)
    except ValueError:
        return Response(status_code=400)

    await issue_service.change_status(issue.id, status_uuid)

    # Return updated issue row for HTMX swap
    templates = get_templates()
    updated_issue = await issue_service.get_issue(issue.id)

    return templates.TemplateResponse(
        request=request,
        name="issues/partials/issue_row.html",
        context={
            "issue": updated_issue,
            "current_user": current_user,
        },
    )
