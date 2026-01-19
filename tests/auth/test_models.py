"""Tests for auth models."""

import pytest
from sqlalchemy import select


@pytest.mark.asyncio
async def test_role_has_permission_returns_true_when_permission_exists(
    db_session,
) -> None:
    """Role.has_permission should return True when role has the permission."""
    from groundwork.auth.models import Permission, Role

    permission = Permission(codename="users:read", description="Can read users")
    role = Role(name="TestRole", description="Test role")
    role.permissions.append(permission)

    db_session.add(role)
    await db_session.commit()

    assert role.has_permission("users:read") is True
    assert role.has_permission("users:write") is False


@pytest.mark.asyncio
async def test_user_model_creates_with_role(db_session) -> None:
    """User should be created with a role."""
    from groundwork.auth.models import Role, User

    role = Role(name="Member", description="Regular member")
    db_session.add(role)
    await db_session.commit()

    user = User(
        email="test@example.com",
        hashed_password="hashed",
        first_name="Test",
        last_name="User",
        role_id=role.id,
    )
    db_session.add(user)
    await db_session.commit()

    result = await db_session.execute(
        select(User).where(User.email == "test@example.com")
    )
    fetched_user = result.scalar_one()

    assert fetched_user.first_name == "Test"
    assert fetched_user.role_id == role.id
