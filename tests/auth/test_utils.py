"""Tests for auth utilities."""


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
