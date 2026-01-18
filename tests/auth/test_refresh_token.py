"""Tests for RefreshToken model."""

from datetime import UTC, datetime, timedelta

import pytest


@pytest.mark.asyncio
async def test_refresh_token_created_for_user(db_session) -> None:
    """RefreshToken should be created and linked to user."""
    from groundwork.auth.models import RefreshToken, Role, User

    role = Role(name="Member", description="Member role")
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

    token = RefreshToken(
        user_id=user.id,
        token_hash="hashed_token_value",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db_session.add(token)
    await db_session.commit()

    assert token.user_id == user.id
    assert token.revoked_at is None
