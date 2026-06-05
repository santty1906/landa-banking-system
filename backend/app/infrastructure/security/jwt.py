"""JWT helpers for access/refresh token handling with typed claims."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import Enum
from uuid import uuid4

from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenPayload(BaseModel):
    """Common JWT claims used by both access and refresh tokens."""

    sub: str | None = None
    token_type: TokenType
    exp: int
    iat: int
    jti: str
    sid: str | None = None
    previous_jti: str | None = None


def _create_token(
    *,
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    additional_claims: dict | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    expire = now + expires_delta

    payload = {
        "sub": subject,
        "token_type": token_type.value,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid4()),
    }
    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, additional_claims: dict | None = None) -> str:
    """Create short-lived access tokens for API authorization."""
    settings = get_settings()
    return _create_token(
        subject=subject,
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        additional_claims=additional_claims,
    )


def create_refresh_token(subject: str, additional_claims: dict | None = None) -> str:
    """Create long-lived refresh tokens for session renewal workflows."""
    settings = get_settings()
    return _create_token(
        subject=subject,
        token_type=TokenType.REFRESH,
        expires_delta=timedelta(minutes=settings.refresh_token_expire_minutes),
        additional_claims=additional_claims,
    )


def decode_token(token: str) -> TokenPayload:
    """Decode and validate token claims into a typed payload."""
    settings = get_settings()
    try:
        raw_payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return TokenPayload.model_validate(raw_payload)
    except (JWTError, ValidationError) as exc:
        raise AuthenticationError("Invalid or expired token") from exc


def build_refresh_rotation_claims(previous_jti: str | None = None) -> dict[str, str | None]:
    """Claims that link rotated refresh tokens for replay analysis."""
    return {"previous_jti": previous_jti}


def token_expiration_datetime(exp: int) -> datetime:
    """Convert UNIX expiration timestamps into timezone-aware datetimes."""
    return datetime.fromtimestamp(exp, tz=UTC)
