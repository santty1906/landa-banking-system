"""Password hashing utilities with Argon2id default and BCrypt fallback."""

from __future__ import annotations

from passlib.context import CryptContext

from app.core.exceptions import AuthenticationError

pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    default="argon2",
    deprecated="auto",
)


class PasswordHasher:
    """Encapsulates password hashing for easier testing and future swaps."""

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as exc:  # pragma: no cover - defensive path for malformed hashes
            raise AuthenticationError("Invalid credentials") from exc
