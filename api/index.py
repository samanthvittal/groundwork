"""Vercel entrypoint for FastAPI application."""

from groundwork.main import app

# Export for Vercel
__all__ = ["app"]
