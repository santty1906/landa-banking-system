"""Domain entities for authentication context and session validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.auth.types import AuthMethod


@dataclass(slots=True)
class AuthContext:
    """Validated authentication context attached to protected requests."""

    user_id: str
    email: str
    is_active: bool
    auth_method: AuthMethod
    session_id: str
    session_created_at: datetime
    token_expiration: datetime
    last_login_at: datetime | None
