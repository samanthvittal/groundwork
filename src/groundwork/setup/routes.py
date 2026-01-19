"""Setup wizard API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from groundwork.core.database import get_db
from groundwork.setup.schemas import (
    AdminCreateRequest,
    AdminUserResponse,
    InstanceConfigResponse,
    InstanceSettingsRequest,
    MessageResponse,
    SetupStatusResponse,
    SmtpConfigRequest,
)
from groundwork.setup.services import SetupService

router = APIRouter(tags=["setup"])


async def check_setup_not_complete(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Dependency to check that setup is not already complete.

    Raises HTTPException 403 if setup is already complete.
    """
    service = SetupService(db)
    if await service.is_setup_complete():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Setup is already complete",
        )


@router.get("/status", response_model=SetupStatusResponse)
async def get_status(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SetupStatusResponse:
    """Get the current setup status.

    Returns the setup completion status and current step.
    Steps are: welcome, instance, admin, smtp, complete
    """
    service = SetupService(db)
    status_data = await service.get_setup_status()
    return SetupStatusResponse(**status_data)


@router.post("/instance", response_model=InstanceConfigResponse)
async def save_instance_settings(
    request: InstanceSettingsRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(check_setup_not_complete)],
) -> InstanceConfigResponse:
    """Save instance settings.

    Creates or updates the instance name and base URL.
    """
    service = SetupService(db)
    config = await service.save_instance_settings(
        instance_name=request.instance_name,
        base_url=str(request.base_url),
    )
    return InstanceConfigResponse.model_validate(config)


@router.post(
    "/admin", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED
)
async def create_admin(
    request: AdminCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(check_setup_not_complete)],
) -> AdminUserResponse:
    """Create the initial admin user.

    Creates an Admin role with full permissions and the admin user.
    """
    # Validate password length (spec requires 400 for password too short)
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    service = SetupService(db)
    user = await service.create_admin_user(
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        password=request.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Admin user already exists",
        )

    return AdminUserResponse.model_validate(user)


@router.post("/smtp", response_model=InstanceConfigResponse)
async def configure_smtp(
    request: SmtpConfigRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(check_setup_not_complete)],
) -> InstanceConfigResponse:
    """Configure SMTP settings.

    Sets up SMTP for sending emails.
    """
    service = SetupService(db)
    config = await service.configure_smtp(
        smtp_host=request.smtp_host,
        smtp_port=request.smtp_port,
        smtp_username=request.smtp_username,
        smtp_password=request.smtp_password,
        smtp_from_address=request.smtp_from_address,
    )

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instance settings must be configured first",
        )

    return InstanceConfigResponse.model_validate(config)


@router.post("/skip-smtp", response_model=MessageResponse)
async def skip_smtp(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(check_setup_not_complete)],
) -> MessageResponse:
    """Skip SMTP configuration.

    Marks SMTP as skipped - email features will be disabled.
    """
    service = SetupService(db)
    result = await service.skip_smtp()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instance settings must be configured first",
        )

    return MessageResponse(message="SMTP configuration skipped")


@router.post("/complete", response_model=InstanceConfigResponse)
async def complete_setup(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(check_setup_not_complete)],
) -> InstanceConfigResponse:
    """Complete the setup process.

    Requires instance settings and admin user to be configured.
    """
    service = SetupService(db)
    config = await service.complete_setup()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prerequisites not met: instance settings and admin user required",
        )

    return InstanceConfigResponse.model_validate(config)
