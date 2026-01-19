"""Placeholder routes for unimplemented features."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response

from groundwork.auth.dependencies import get_current_user
from groundwork.auth.models import User
from groundwork.core.templates import get_templates

router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
@router.get("/projects", response_class=HTMLResponse)
@router.get("/tasks", response_class=HTMLResponse)
@router.get("/calendar", response_class=HTMLResponse)
@router.get("/team", response_class=HTMLResponse)
@router.get("/messages", response_class=HTMLResponse)
@router.get("/settings", response_class=HTMLResponse)
async def coming_soon(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Placeholder for unimplemented pages."""
    templates = get_templates()
    return templates.TemplateResponse(
        request=request,
        name="pages/coming_soon.html",
        context={"current_user": current_user},
    )
