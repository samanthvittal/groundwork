"""Tests for database module."""


def test_base_class_exists() -> None:
    """Base declarative class should be importable."""
    from groundwork.core.database import Base

    assert Base is not None
    assert hasattr(Base, "metadata")


def test_get_db_is_async_generator() -> None:
    """get_db should be an async generator function."""
    import inspect

    from groundwork.core.database import get_db

    assert inspect.isasyncgenfunction(get_db)
