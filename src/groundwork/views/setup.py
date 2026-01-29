"""Setup wizard view routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from groundwork.auth.models import Role
from groundwork.core.database import get_db
from groundwork.core.templates import get_templates
from groundwork.setup.middleware import reset_setup_cache
from groundwork.setup.services import SetupService

router = APIRouter()


async def get_setup_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SetupService:
    """Get setup service instance."""
    return SetupService(db)


@router.get("/setup", response_class=HTMLResponse)
async def setup_welcome(
    request: Request,
    service: Annotated[SetupService, Depends(get_setup_service)],
) -> Response:
    """Setup welcome page."""
    status = await service.get_setup_status()
    if status["setup_completed"]:
        return RedirectResponse(url="/login", status_code=303)

    templates = get_templates()
    return templates.TemplateResponse(
        request=request,
        name="setup/welcome.html",
    )


@router.get("/setup/instance", response_class=HTMLResponse)
async def setup_instance_form(
    request: Request,
    service: Annotated[SetupService, Depends(get_setup_service)],
) -> Response:
    """Instance settings form."""
    status = await service.get_setup_status()
    if status["setup_completed"]:
        return RedirectResponse(url="/login", status_code=303)

    templates = get_templates()
    return templates.TemplateResponse(
        request=request,
        name="setup/instance.html",
        context={"base_url": str(request.base_url).rstrip("/")},
    )


@router.post("/setup/instance", response_class=HTMLResponse)
async def setup_instance_submit(
    request: Request,
    service: Annotated[SetupService, Depends(get_setup_service)],
    instance_name: Annotated[str, Form()],
    base_url: Annotated[str, Form()],
) -> Response:
    """Process instance settings."""
    try:
        await service.save_instance_settings(instance_name, base_url)
        return RedirectResponse(url="/setup/admin", status_code=303)
    except Exception as e:
        templates = get_templates()
        return templates.TemplateResponse(
            request=request,
            name="setup/instance.html",
            context={
                "error": str(e),
                "instance_name": instance_name,
                "base_url": base_url,
            },
        )


@router.get("/setup/admin", response_class=HTMLResponse)
async def setup_admin_form(
    request: Request,
    service: Annotated[SetupService, Depends(get_setup_service)],
) -> Response:
    """Admin account form."""
    status = await service.get_setup_status()
    if status["setup_completed"]:
        return RedirectResponse(url="/login", status_code=303)
    if status["current_step"] == "welcome":
        return RedirectResponse(url="/setup/instance", status_code=303)

    templates = get_templates()
    return templates.TemplateResponse(
        request=request,
        name="setup/admin.html",
    )


@router.post("/setup/admin", response_class=HTMLResponse)
async def setup_admin_submit(
    request: Request,
    service: Annotated[SetupService, Depends(get_setup_service)],
    email: Annotated[str, Form()],
    first_name: Annotated[str, Form()],
    last_name: Annotated[str, Form()],
    password: Annotated[str, Form()],
    password_confirm: Annotated[str, Form()],
) -> Response:
    """Process admin account creation."""
    templates = get_templates()

    if password != password_confirm:
        return templates.TemplateResponse(
            request=request,
            name="setup/admin.html",
            context={
                "error": "Passwords do not match",
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            },
        )

    if len(password) < 8:
        return templates.TemplateResponse(
            request=request,
            name="setup/admin.html",
            context={
                "error": "Password must be at least 8 characters",
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            },
        )

    try:
        result = await service.create_admin_user(email, first_name, last_name, password)
        if result is None:
            return templates.TemplateResponse(
                request=request,
                name="setup/admin.html",
                context={
                    "error": "Admin user already exists",
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
        return RedirectResponse(url="/setup/smtp", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="setup/admin.html",
            context={
                "error": str(e),
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            },
        )


@router.get("/setup/smtp", response_class=HTMLResponse)
async def setup_smtp_form(
    request: Request,
    service: Annotated[SetupService, Depends(get_setup_service)],
) -> Response:
    """SMTP configuration form."""
    status = await service.get_setup_status()
    if status["setup_completed"]:
        return RedirectResponse(url="/login", status_code=303)
    if status["current_step"] in ["welcome", "admin"]:
        return RedirectResponse(url="/setup", status_code=303)

    templates = get_templates()
    return templates.TemplateResponse(
        request=request,
        name="setup/smtp.html",
    )


@router.post("/setup/smtp", response_class=HTMLResponse)
async def setup_smtp_submit(
    request: Request,
    service: Annotated[SetupService, Depends(get_setup_service)],
    smtp_host: Annotated[str, Form()] = "",
    smtp_port: Annotated[int, Form()] = 587,
    smtp_username: Annotated[str | None, Form()] = None,
    smtp_password: Annotated[str | None, Form()] = None,
    smtp_from_address: Annotated[str, Form()] = "",
) -> Response:
    """Process SMTP configuration."""
    try:
        if smtp_host:
            await service.configure_smtp(
                smtp_host=smtp_host,
                smtp_port=smtp_port,
                smtp_username=smtp_username,
                smtp_password=smtp_password,
                smtp_from_address=smtp_from_address,
            )
        await service.complete_setup()
        reset_setup_cache()
        return RedirectResponse(url="/setup/complete", status_code=303)
    except Exception as e:
        templates = get_templates()
        return templates.TemplateResponse(
            request=request,
            name="setup/smtp.html",
            context={
                "error": str(e),
                "smtp_host": smtp_host,
                "smtp_port": smtp_port,
                "smtp_username": smtp_username,
                "smtp_from_address": smtp_from_address,
            },
        )


@router.get("/setup/complete", response_class=HTMLResponse)
async def setup_complete(
    request: Request,
    service: Annotated[SetupService, Depends(get_setup_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Setup complete page."""
    # Complete setup if not already done (for skip SMTP flow)
    status = await service.get_setup_status()
    if not status["setup_completed"]:
        await service.complete_setup()
        reset_setup_cache()

    config = await service._get_instance_config()

    # Get admin email by looking up Admin role users
    admin_email = "Unknown"
    result = await db.execute(
        select(Role).where(Role.name == "Admin").options(selectinload(Role.users))
    )
    admin_role = result.scalar_one_or_none()
    if admin_role and admin_role.users:
        admin_email = admin_role.users[0].email

    templates = get_templates()
    return templates.TemplateResponse(
        request=request,
        name="setup/complete.html",
        context={
            "instance_name": config.instance_name if config else "Groundwork",
            "admin_email": admin_email,
            "smtp_configured": config.smtp_configured if config else False,
        },
    )
