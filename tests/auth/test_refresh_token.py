"""Tests for RefreshToken model."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload


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


@pytest.mark.asyncio
async def test_refresh_token_with_expired_date(db_session) -> None:
    """RefreshToken can be created with an expired date."""
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

    # Create token with past expiration date
    expired_time = datetime.now(UTC) - timedelta(days=1)
    token = RefreshToken(
        user_id=user.id,
        token_hash="expired_token_hash",
        expires_at=expired_time,
    )
    db_session.add(token)
    await db_session.commit()

    assert token.expires_at == expired_time
    assert token.expires_at < datetime.now(UTC)


@pytest.mark.asyncio
async def test_refresh_token_revocation(db_session) -> None:
    """RefreshToken can be revoked by setting revoked_at."""
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
        token_hash="token_to_revoke",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db_session.add(token)
    await db_session.commit()

    # Token should not be revoked initially
    assert token.revoked_at is None

    # Revoke the token
    revoke_time = datetime.now(UTC)
    token.revoked_at = revoke_time
    await db_session.commit()

    assert token.revoked_at == revoke_time


@pytest.mark.asyncio
async def test_refresh_token_user_relationship(db_session) -> None:
    """RefreshToken.user relationship should load the associated user."""
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
        token_hash="token_with_user",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db_session.add(token)
    await db_session.commit()

    # Query the token with user relationship loaded
    result = await db_session.execute(
        select(RefreshToken)
        .options(selectinload(RefreshToken.user))
        .where(RefreshToken.id == token.id)
    )
    loaded_token = result.scalar_one()

    assert loaded_token.user is not None
    assert loaded_token.user.id == user.id
    assert loaded_token.user.email == "test@example.com"
