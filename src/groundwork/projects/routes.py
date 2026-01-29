"""Project management API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.dependencies import CurrentUser
from groundwork.core.database import get_db
from groundwork.projects.models import ProjectStatus
from groundwork.projects.schemas import (
    ProjectCreate,
    ProjectDetailResponse,
    ProjectMemberAdd,
    ProjectMemberResponse,
    ProjectMemberUpdate,
    ProjectResponse,
    ProjectUpdate,
)
from groundwork.projects.services import ProjectService

router = APIRouter(tags=["projects"])


def parse_uuid(project_id: str) -> UUID:
    """Parse and validate UUID, raise 404 for invalid UUIDs."""
    try:
        return UUID(project_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from None


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
    status: ProjectStatus | None = None,
    mine: bool = False,
) -> list[ProjectResponse]:
    """List projects.

    If `mine=True`, returns only projects where user is owner or member.
    Otherwise returns all active projects (admin only).
    """
    service = ProjectService(db)

    if mine:
        projects = await service.list_user_projects(
            user_id=current_user.id, skip=skip, limit=limit
        )
    elif current_user.is_admin:
        projects = await service.list_projects(skip=skip, limit=limit, status=status)
    else:
        # Non-admins can only see their own projects
        projects = await service.list_user_projects(
            user_id=current_user.id, skip=skip, limit=limit
        )

    return [ProjectResponse.model_validate(p) for p in projects]


@router.post(
    "/", response_model=ProjectDetailResponse, status_code=status.HTTP_201_CREATED
)
async def create_project(
    request: ProjectCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectDetailResponse:
    """Create a new project.

    The current user becomes the project owner.
    """
    service = ProjectService(db)
    project = await service.create_project(
        key=request.key,
        name=request.name,
        owner_id=current_user.id,
        description=request.description,
        visibility=request.visibility,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project with this key already exists",
        )

    return ProjectDetailResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectDetailResponse:
    """Get project by ID.

    User must have access to the project.
    """
    uuid = parse_uuid(project_id)
    service = ProjectService(db)
    project = await service.get_project(uuid)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check access
    if not current_user.is_admin:
        can_access = await service.user_can_access(uuid, current_user.id)
        if not can_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project",
            )

    return ProjectDetailResponse.model_validate(project)


@router.get("/key/{project_key}", response_model=ProjectDetailResponse)
async def get_project_by_key(
    project_key: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectDetailResponse:
    """Get project by key.

    User must have access to the project.
    """
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

    return ProjectDetailResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectDetailResponse)
async def update_project(
    project_id: str,
    request: ProjectUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectDetailResponse:
    """Update project fields.

    Requires admin permission on the project.
    """
    uuid = parse_uuid(project_id)
    service = ProjectService(db)

    # Check admin access
    if not current_user.is_admin:
        can_admin = await service.user_can_admin(uuid, current_user.id)
        if not can_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have admin access to this project",
            )

    project = await service.update_project(
        project_id=uuid,
        name=request.name,
        description=request.description,
        visibility=request.visibility,
        status=request.status,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return ProjectDetailResponse.model_validate(project)


@router.post("/{project_id}/archive", response_model=ProjectDetailResponse)
async def archive_project(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectDetailResponse:
    """Archive a project.

    Requires owner permission on the project.
    """
    uuid = parse_uuid(project_id)
    service = ProjectService(db)

    # Only owner can archive
    if not current_user.is_admin:
        is_owner = await service.user_is_owner(uuid, current_user.id)
        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the project owner can archive the project",
            )

    project = await service.archive_project(uuid)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return ProjectDetailResponse.model_validate(project)


@router.post("/{project_id}/restore", response_model=ProjectDetailResponse)
async def restore_project(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectDetailResponse:
    """Restore an archived project.

    Requires owner permission on the project.
    """
    uuid = parse_uuid(project_id)
    service = ProjectService(db)

    # Check project exists and is archived
    project = await service.get_project(uuid)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if project.status != ProjectStatus.ARCHIVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project is not archived",
        )

    # Only owner can restore
    if not current_user.is_admin:
        is_owner = await service.user_is_owner(uuid, current_user.id)
        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the project owner can restore the project",
            )

    restored = await service.restore_project(uuid)
    return ProjectDetailResponse.model_validate(restored)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Soft delete a project.

    Requires owner permission on the project.
    """
    uuid = parse_uuid(project_id)
    service = ProjectService(db)

    # Only owner can delete
    if not current_user.is_admin:
        is_owner = await service.user_is_owner(uuid, current_user.id)
        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the project owner can delete the project",
            )

    result = await service.delete_project(uuid)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Member management routes


@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
async def list_project_members(
    project_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ProjectMemberResponse]:
    """List project members.

    User must have access to the project.
    """
    uuid = parse_uuid(project_id)
    service = ProjectService(db)

    # Check access
    if not current_user.is_admin:
        can_access = await service.user_can_access(uuid, current_user.id)
        if not can_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project",
            )

    members = await service.list_project_members(uuid)
    return [ProjectMemberResponse.model_validate(m) for m in members]


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_member(
    project_id: str,
    request: ProjectMemberAdd,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectMemberResponse:
    """Add a member to a project.

    Requires admin permission on the project.
    """
    uuid = parse_uuid(project_id)
    service = ProjectService(db)

    # Check admin access
    if not current_user.is_admin:
        can_admin = await service.user_can_admin(uuid, current_user.id)
        if not can_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have admin access to this project",
            )

    member = await service.add_member(
        project_id=uuid,
        user_id=request.user_id,
        role=request.role,
    )

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this project",
        )

    return ProjectMemberResponse.model_validate(member)


@router.patch("/{project_id}/members/{user_id}", response_model=ProjectMemberResponse)
async def update_project_member(
    project_id: str,
    user_id: str,
    request: ProjectMemberUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectMemberResponse:
    """Update a member's role.

    Requires admin permission on the project.
    """
    project_uuid = parse_uuid(project_id)
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        ) from None

    service = ProjectService(db)

    # Check admin access
    if not current_user.is_admin:
        can_admin = await service.user_can_admin(project_uuid, current_user.id)
        if not can_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have admin access to this project",
            )

    member = await service.update_member_role(
        project_id=project_uuid,
        user_id=user_uuid,
        role=request.role,
    )

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    return ProjectMemberResponse.model_validate(member)


@router.delete(
    "/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_project_member(
    project_id: str,
    user_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Remove a member from a project.

    Requires admin permission on the project.
    Users can remove themselves from a project.
    """
    project_uuid = parse_uuid(project_id)
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        ) from None

    service = ProjectService(db)

    # Check if user is removing themselves (always allowed)
    is_self = user_uuid == current_user.id

    if not is_self and not current_user.is_admin:
        can_admin = await service.user_can_admin(project_uuid, current_user.id)
        if not can_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have admin access to this project",
            )

    result = await service.remove_member(project_uuid, user_uuid)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
