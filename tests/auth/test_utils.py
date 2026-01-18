"""Tests for auth utilities."""

from uuid import uuid4


def test_hash_password_returns_hashed_value() -> None:
    """hash_password should return a hashed string."""
    from groundwork.auth.utils import hash_password

    password = "mysecretpassword"
    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$argon2")


def test_verify_password_returns_true_for_correct_password() -> None:
    """verify_password should return True for correct password."""
    from groundwork.auth.utils import hash_password, verify_password

    password = "mysecretpassword"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token_returns_jwt() -> None:
    """create_access_token should return a valid JWT."""
    from groundwork.auth.utils import create_access_token, decode_token

    user_id = uuid4()
    token = create_access_token(user_id=str(user_id))

    assert token is not None
    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"


def test_create_refresh_token_returns_jwt() -> None:
    """create_refresh_token should return a valid JWT with longer expiry."""
    from groundwork.auth.utils import create_refresh_token, decode_token

    user_id = uuid4()
    token = create_refresh_token(user_id=str(user_id))

    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"


def test_decode_token_returns_none_for_invalid_token() -> None:
    """decode_token should return None for invalid tokens."""
    from groundwork.auth.utils import decode_token

    result = decode_token("invalid.token.here")
    assert result is None
