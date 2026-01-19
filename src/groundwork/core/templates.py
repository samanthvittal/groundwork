"""Jinja2 template configuration."""

from pathlib import Path

from fastapi.templating import Jinja2Templates

# Path configuration for templates
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

# Initialize Jinja2Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def get_templates() -> Jinja2Templates:
    """Get the configured Jinja2Templates instance."""
    return templates
