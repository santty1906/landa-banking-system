import pytest

from app.core.exceptions import AuthenticationError
from app.infrastructure.security.password import PasswordHasher


def test_hash_and_verify_password_success() -> None:
    hasher = PasswordHasher()

    hashed = hasher.hash_password("securePassword123")

    assert hashed != "securePassword123"
    assert hasher.verify_password("securePassword123", hashed)


def test_verify_password_invalid_hash_raises_auth_error() -> None:
    hasher = PasswordHasher()

    with pytest.raises(AuthenticationError):
        hasher.verify_password("securePassword123", "not_a_valid_hash")
