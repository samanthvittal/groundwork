"""Role management API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.auth.dependencies import CurrentUser, require_permission
from groundwork.auth.models import User
from groundwork.core.database import get_db
from groundwork.roles.schemas import (
    PermissionResponse,
    RoleCreate,
    RoleDetailResponse,
    RoleResponse,
    RoleUpdate,
)
from groundwork.roles.services import RoleService

router = APIRouter(tags=["roles"])


# Permission check function that wraps require_permission with CurrentUser dependency
def check_roles_manage(current_user: CurrentUser) -> User:
    """Check roles:manage permission."""
    return require_permission("roles:manage")(current_user)


def parse_uuid(role_id: str) -> UUID:
    """Parse and validate UUID, raise 404 for invalid UUIDs."""
    try:
        return UUID(role_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        ) from None


@router.get("/permissions", response_model=list[PermissionResponse])
async def list_permissions(
    _: Annotated[User, Depends(check_roles_manage)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PermissionResponse]:
    """List all available permissions.

    Requires `roles:manage` permission.
    """
    service = RoleService(db)
    permissions = await service.list_permissions()
    return [PermissionResponse.model_validate(perm) for perm in permissions]


@router.get("/", response_model=list[RoleResponse])
async def list_roles(
    _: Annotated[User, Depends(check_roles_manage)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[RoleResponse]:
    """List all roles.

    Requires `roles:manage` permission.
    """
    service = RoleService(db)
    roles = await service.list_roles()
    return [RoleResponse.model_validate(role) for role in roles]


@router.post(
    "/", response_model=RoleDetailResponse, status_code=status.HTTP_201_CREATED
)
async def create_role(
    request: RoleCreate,
    _: Annotated[User, Depends(check_roles_manage)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoleDetailResponse:
    """Create a new custom role.

    Requires `roles:manage` permission.
    """
    service = RoleService(db)
    role = await service.create_role(
        name=request.name,
        description=request.description,
        permission_ids=request.permission_ids,
    )

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role with this name already exists",
        )

    return RoleDetailResponse.model_validate(role)


@router.get("/{role_id}", response_model=RoleDetailResponse)
async def get_role(
    role_id: str,
    _: Annotated[User, Depends(check_roles_manage)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoleDetailResponse:
    """Get role details with permissions.

    Requires `roles:manage` permission.
    """
    uuid = parse_uuid(role_id)
    service = RoleService(db)
    role = await service.get_role(uuid)

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    return RoleDetailResponse.model_validate(role)


@router.patch("/{role_id}", response_model=RoleDetailResponse)
async def update_role(
    role_id: str,
    request: RoleUpdate,
    _: Annotated[User, Depends(check_roles_manage)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoleDetailResponse:
    """Update role fields.

    Requires `roles:manage` permission.
    """
    uuid = parse_uuid(role_id)
    service = RoleService(db)
    role = await service.update_role(
        role_id=uuid,
        name=request.name,
        description=request.description,
        permission_ids=request.permission_ids,
    )

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    return RoleDetailResponse.model_validate(role)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: str,
    _: Annotated[User, Depends(check_roles_manage)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Delete a custom role.

    System roles cannot be deleted.
    Requires `roles:manage` permission.
    """
    uuid = parse_uuid(role_id)
    service = RoleService(db)
    result = await service.delete_role(uuid)

    if result == "system":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system role",
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
