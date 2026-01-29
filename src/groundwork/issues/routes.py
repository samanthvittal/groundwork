"""Issue management API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.dependencies import CurrentUser
from groundwork.core.database import get_db
from groundwork.issues.models import Priority
from groundwork.issues.schemas import (
    IssueCreate,
    IssueDetailResponse,
    IssueFilters,
    IssueLabelAdd,
    IssueResponse,
    IssueSummaryResponse,
    IssueTypeResponse,
    IssueUpdate,
    LabelCreate,
    LabelResponse,
    LabelUpdate,
    StatusResponse,
    SubtaskCreate,
    SubtaskLink,
)
from groundwork.issues.services import (
    IssueService,
    IssueTypeService,
    LabelService,
    StatusService,
)
from groundwork.projects.services import ProjectService

router = APIRouter(tags=["issues"])


# =============================================================================
# Helper Functions
# =============================================================================


async def get_project_by_key(
    project_key: str,
    db: AsyncSession,
    current_user: CurrentUser,
) -> "Project":
    """Get project by key and verify access."""
    from groundwork.projects.models import Project

    service = ProjectService(db)
    project = await service.get_project_by_key(project_key.upper())

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check access
    if not current_user.is_admin:
        can_access = await service.user_can_access(project.id, current_user.id)
        if not can_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project",
            )

    return project


async def get_issue_by_key_or_404(
    issue_key: str,
    db: AsyncSession,
    current_user: CurrentUser,
) -> "Issue":
    """Get issue by key and verify access."""
    from groundwork.issues.models import Issue

    service = IssueService(db)
    issue = await service.get_issue_by_key(issue_key.upper())

    if issue is None or issue.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found",
        )

    # Check access via project membership
    if not current_user.is_admin:
        can_view = await service.user_can_view(issue.id, current_user.id)
        if not can_view:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this issue",
            )

    return issue


# =============================================================================
# Issue Types & Statuses (Config)
# =============================================================================


@router.get("/projects/{project_key}/issue-types", response_model=list[IssueTypeResponse])
async def list_issue_types(
    project_key: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[IssueTypeResponse]:
    """List available issue types for a project.

    Returns both system defaults and project-specific types.
    """
    project = await get_project_by_key(project_key, db, current_user)
    service = IssueTypeService(db)
    types = await service.list_issue_types(project.id)
    return [IssueTypeResponse.model_validate(t) for t in types]


@router.get("/projects/{project_key}/statuses", response_model=list[StatusResponse])
async def list_statuses(
    project_key: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[StatusResponse]:
    """List available statuses for a project.

    Returns both system defaults and project-specific statuses.
    """
    project = await get_project_by_key(project_key, db, current_user)
    service = StatusService(db)
    statuses = await service.list_statuses(project.id)
    return [StatusResponse.model_validate(s) for s in statuses]


# =============================================================================
# Issue CRUD
# =============================================================================


@router.get("/projects/{project_key}/issues", response_model=list[IssueSummaryResponse])
async def list_issues(
    project_key: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    status: Annotated[str | None, Query(description="Filter by status ID or category")] = None,
    type: Annotated[str | None, Query(description="Filter by type ID")] = None,
    assignee: Annotated[str | None, Query(description="'me', 'unassigned', or user ID")] = None,
    priority: Annotated[str | None, Query(description="Filter by priority")] = None,
    label: Annotated[UUID | None, Query(description="Filter by label ID")] = None,
    parent: Annotated[str | None, Query(description="'none' for root issues, or issue key")] = None,
    q: Annotated[str | None, Query(description="Search query")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[IssueSummaryResponse]:
    """List issues in a project with optional filters."""
    project = await get_project_by_key(project_key, db, current_user)
    service = IssueService(db)

    # Parse filters
    status_id = None
    if status is not None:
        try:
            status_id = UUID(status)
        except ValueError:
            pass  # Could be a category name, but we'll skip for now

    type_id = None
    if type is not None:
        try:
            type_id = UUID(type)
        except ValueError:
            pass

    assignee_id = None
    if assignee == "me":
        assignee_id = current_user.id
    elif assignee == "unassigned":
        assignee_id = None  # Will need special handling in service
    elif assignee is not None:
        try:
            assignee_id = UUID(assignee)
        except ValueError:
            pass

    priority_filter = None
    if priority is not None:
        try:
            priority_filter = Priority(priority)
        except ValueError:
            pass

    parent_id = ...  # Sentinel for "any"
    if parent == "none":
        parent_id = None  # Root issues only
    elif parent is not None:
        # Parse as issue key
        parent_issue = await service.get_issue_by_key(parent.upper())
        if parent_issue:
            parent_id = parent_issue.id

    issues = await service.list_issues(
        project_id=project.id,
        status_id=status_id,
        type_id=type_id,
        assignee_id=assignee_id,
        priority=priority_filter,
        label_id=label,
        parent_id=parent_id,
        search=q,
        skip=(page - 1) * per_page,
        limit=per_page,
    )

    return [IssueSummaryResponse.model_validate(i) for i in issues]


@router.post(
    "/projects/{project_key}/issues",
    response_model=IssueResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_issue(
    project_key: str,
    request: IssueCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IssueResponse:
    """Create a new issue in a project.

    The current user becomes the reporter.
    """
    project = await get_project_by_key(project_key, db, current_user)

    # Verify user has at least MEMBER role to create issues
    if not current_user.is_admin:
        project_service = ProjectService(db)
        can_admin = await project_service.user_can_admin(project.id, current_user.id)
        member = await project_service.get_member(project.id, current_user.id)
        if member is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a project member to create issues",
            )

    service = IssueService(db)
    issue = await service.create_issue(
        project_id=project.id,
        title=request.title,
        type_id=request.type_id,
        reporter_id=current_user.id,
        status_id=request.status_id,
        priority=request.priority,
        description=request.description,
        assignee_id=request.assignee_id,
        parent_id=request.parent_id,
    )

    return IssueResponse.model_validate(issue)


@router.get("/issues/{issue_key}", response_model=IssueDetailResponse)
async def get_issue(
    issue_key: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IssueDetailResponse:
    """Get issue by key with full details including subtasks."""
    issue = await get_issue_by_key_or_404(issue_key, db, current_user)

    # Build response with subtask count
    response = IssueDetailResponse.model_validate(issue)
    response.subtasks = [IssueSummaryResponse.model_validate(s) for s in issue.subtasks]

    return response


@router.patch("/issues/{issue_key}", response_model=IssueResponse)
async def update_issue(
    issue_key: str,
    request: IssueUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IssueResponse:
    """Update issue fields."""
    issue = await get_issue_by_key_or_404(issue_key, db, current_user)

    # Check edit permission
    service = IssueService(db)
    if not current_user.is_admin:
        can_edit = await service.user_can_edit(issue.id, current_user.id)
        if not can_edit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to edit this issue",
            )

    # Build update kwargs - use request.model_fields_set to know what was provided
    kwargs = {}
    if "title" in request.model_fields_set:
        kwargs["title"] = request.title
    if "description" in request.model_fields_set:
        kwargs["description"] = request.description
    if "type_id" in request.model_fields_set:
        kwargs["type_id"] = request.type_id
    if "status_id" in request.model_fields_set:
        kwargs["status_id"] = request.status_id
    if "priority" in request.model_fields_set:
        kwargs["priority"] = request.priority
    if "assignee_id" in request.model_fields_set:
        kwargs["assignee_id"] = request.assignee_id
    if "parent_id" in request.model_fields_set:
        kwargs["parent_id"] = request.parent_id

    updated = await service.update_issue(issue.id, **kwargs)
    return IssueResponse.model_validate(updated)


@router.delete("/issues/{issue_key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_issue(
    issue_key: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Soft delete an issue."""
    issue = await get_issue_by_key_or_404(issue_key, db, current_user)

    # Check delete permission (ADMIN+ or reporter)
    service = IssueService(db)
    if not current_user.is_admin:
        can_delete = await service.user_can_delete(issue.id, current_user.id)
        # Also allow reporter to delete
        is_reporter = issue.reporter_id == current_user.id
        if not can_delete and not is_reporter:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this issue",
            )

    await service.delete_issue(issue.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =============================================================================
# Subtask Management
# =============================================================================


@router.get("/issues/{issue_key}/subtasks", response_model=list[IssueSummaryResponse])
async def list_subtasks(
    issue_key: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[IssueSummaryResponse]:
    """List subtasks of an issue."""
    issue = await get_issue_by_key_or_404(issue_key, db, current_user)
    service = IssueService(db)
    subtasks = await service.list_subtasks(issue.id)
    return [IssueSummaryResponse.model_validate(s) for s in subtasks]


@router.post(
    "/issues/{issue_key}/subtasks",
    response_model=IssueResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_or_link_subtask(
    issue_key: str,
    request: SubtaskCreate | SubtaskLink,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IssueResponse:
    """Create a new subtask or link an existing issue as subtask.

    If request contains `issue_id`, links existing issue.
    Otherwise, creates a new subtask with the provided fields.
    """
    parent = await get_issue_by_key_or_404(issue_key, db, current_user)
    service = IssueService(db)

    # Check edit permission on parent
    if not current_user.is_admin:
        can_edit = await service.user_can_edit(parent.id, current_user.id)
        if not can_edit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to add subtasks to this issue",
            )

    # Check if linking existing issue or creating new
    if isinstance(request, SubtaskLink) or hasattr(request, "issue_id"):
        # Link existing issue
        link_request = request if isinstance(request, SubtaskLink) else SubtaskLink(issue_id=request.issue_id)
        subtask = await service.get_issue(link_request.issue_id)

        if subtask is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Issue to link not found",
            )

        # Verify same project
        if subtask.project_id != parent.project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot link issues from different projects",
            )

        # Prevent self-linking and circular references
        if subtask.id == parent.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot link issue to itself",
            )

        updated = await service.set_parent(subtask.id, parent.id)
        return IssueResponse.model_validate(updated)
    else:
        # Create new subtask
        create_request = request if isinstance(request, SubtaskCreate) else SubtaskCreate(**request.model_dump())
        subtask = await service.create_issue(
            project_id=parent.project_id,
            title=create_request.title,
            type_id=create_request.type_id,
            reporter_id=current_user.id,
            priority=create_request.priority,
            description=create_request.description,
            assignee_id=create_request.assignee_id,
            parent_id=parent.id,
        )
        return IssueResponse.model_validate(subtask)


@router.delete(
    "/issues/{issue_key}/subtasks/{subtask_key}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unlink_subtask(
    issue_key: str,
    subtask_key: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Unlink a subtask from its parent (does not delete the issue)."""
    parent = await get_issue_by_key_or_404(issue_key, db, current_user)
    service = IssueService(db)

    # Check edit permission on parent
    if not current_user.is_admin:
        can_edit = await service.user_can_edit(parent.id, current_user.id)
        if not can_edit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to manage subtasks of this issue",
            )

    subtask = await service.get_issue_by_key(subtask_key.upper())
    if subtask is None or subtask.parent_id != parent.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subtask not found",
        )

    await service.set_parent(subtask.id, None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =============================================================================
# Label Management (Project)
# =============================================================================


@router.get("/projects/{project_key}/labels", response_model=list[LabelResponse])
async def list_labels(
    project_key: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[LabelResponse]:
    """List all labels in a project."""
    project = await get_project_by_key(project_key, db, current_user)
    service = LabelService(db)
    labels = await service.list_labels(project.id)
    return [LabelResponse.model_validate(l) for l in labels]


@router.post(
    "/projects/{project_key}/labels",
    response_model=LabelResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_label(
    project_key: str,
    request: LabelCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LabelResponse:
    """Create a new label in a project."""
    project = await get_project_by_key(project_key, db, current_user)

    # Check admin permission
    if not current_user.is_admin:
        project_service = ProjectService(db)
        can_admin = await project_service.user_can_admin(project.id, current_user.id)
        if not can_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You need admin access to create labels",
            )

    service = LabelService(db)
    label = await service.create_label(
        project_id=project.id,
        name=request.name,
        color=request.color,
        description=request.description,
    )

    if label is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Label with this name already exists",
        )

    return LabelResponse.model_validate(label)


@router.patch("/labels/{label_id}", response_model=LabelResponse)
async def update_label(
    label_id: UUID,
    request: LabelUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LabelResponse:
    """Update a label."""
    service = LabelService(db)
    label = await service.get_label(label_id)

    if label is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label not found",
        )

    # Check admin permission on the project
    if not current_user.is_admin:
        project_service = ProjectService(db)
        can_admin = await project_service.user_can_admin(label.project_id, current_user.id)
        if not can_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You need admin access to update labels",
            )

    updated = await service.update_label(
        label_id=label_id,
        name=request.name,
        color=request.color,
        description=request.description,
    )

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Label with this name already exists",
        )

    return LabelResponse.model_validate(updated)


@router.delete("/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    label_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Delete a label."""
    service = LabelService(db)
    label = await service.get_label(label_id)

    if label is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label not found",
        )

    # Check admin permission on the project
    if not current_user.is_admin:
        project_service = ProjectService(db)
        can_admin = await project_service.user_can_admin(label.project_id, current_user.id)
        if not can_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You need admin access to delete labels",
            )

    await service.delete_label(label_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =============================================================================
# Label Management (Issue)
# =============================================================================


@router.post(
    "/issues/{issue_key}/labels",
    response_model=IssueResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_label_to_issue(
    issue_key: str,
    request: IssueLabelAdd,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IssueResponse:
    """Add a label to an issue."""
    issue = await get_issue_by_key_or_404(issue_key, db, current_user)
    service = IssueService(db)

    # Check edit permission
    if not current_user.is_admin:
        can_edit = await service.user_can_edit(issue.id, current_user.id)
        if not can_edit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to edit this issue",
            )

    # Verify label exists and belongs to same project
    label_service = LabelService(db)
    label = await label_service.get_label(request.label_id)
    if label is None or label.project_id != issue.project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Label not found",
        )

    updated = await service.add_label(issue.id, request.label_id)
    return IssueResponse.model_validate(updated)


@router.delete(
    "/issues/{issue_key}/labels/{label_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_label_from_issue(
    issue_key: str,
    label_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Remove a label from an issue."""
    issue = await get_issue_by_key_or_404(issue_key, db, current_user)
    service = IssueService(db)

    # Check edit permission
    if not current_user.is_admin:
        can_edit = await service.user_can_edit(issue.id, current_user.id)
        if not can_edit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to edit this issue",
            )

    await service.remove_label(issue.id, label_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
