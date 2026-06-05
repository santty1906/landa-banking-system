"""Authentication domain repository contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.domain.auth.types import AuthMethod


class UserRecord(Protocol):
    id: str
    email: str
    password_hash: str
    is_active: bool
    last_login_at: datetime | None


class AuthSessionRecord(Protocol):
    id: str
    user_id: str
    refresh_jti: str
    auth_method: AuthMethod
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None


class UserRepository(Protocol):
    def get_by_email(self, email: str) -> UserRecord | None: ...

    def get_by_id(self, user_id: str) -> UserRecord | None: ...

    def create(self, *, email: str, password_hash: str, is_active: bool = True) -> UserRecord: ...

    def update_last_login(self, *, user_id: str, at: datetime) -> None: ...


class AuthSessionRepository(Protocol):
    def create(self, *, user_id: str, refresh_jti: str, auth_method: AuthMethod, expires_at: datetime) -> AuthSessionRecord: ...

    def get_active_by_id(self, session_id: str) -> AuthSessionRecord | None: ...

    def get_active_by_refresh_jti(self, refresh_jti: str) -> AuthSessionRecord | None: ...

    def revoke(self, *, session_id: str, reason: str, replaced_by_jti: str | None = None) -> None: ...

    def revoke_all_for_user(self, *, user_id: str, reason: str) -> int: ...
