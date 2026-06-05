"""Authentication request and response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.auth.types import AuthMethod


class CredentialsMixin(BaseModel):
    """Reusable validation for credentials payloads."""

    email: str = Field(min_length=6, max_length=320)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Email must be valid")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        candidate = value.strip()
        if len(candidate) < 8:
            raise ValueError("Password must contain at least 8 characters")
        return candidate


class RegisterRequest(CredentialsMixin):
    pass


class LoginRequest(CredentialsMixin):
    pass


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


class LogoutRequest(BaseModel):
    all_sessions: bool = False


class TokenPairResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int


class LogoutResponse(BaseModel):
    revoked_sessions: int


class SessionResponse(BaseModel):
    user_id: str
    email: str
    is_active: bool
    auth_method: AuthMethod
    session_created_at: datetime
    token_expiration: datetime
    last_login_at: datetime | None
