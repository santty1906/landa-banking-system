"""SQLAlchemy-backed repositories for authentication entities."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.domain.auth.types import AuthMethod
from app.infrastructure.db.models.auth_session import AuthSession
from app.infrastructure.db.models.user import User


class SQLAlchemyUserRepository:
    """Persistence adapter for user authentication records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.scalar(select(User).where(User.id == user_id))

    def create(self, *, email: str, password_hash: str, is_active: bool = True) -> User:
        user = User(email=email, password_hash=password_hash, is_active=is_active)
        self.db.add(user)
        self.db.flush()
        return user

    def update_last_login(self, *, user_id: str, at: datetime) -> None:
        self.db.execute(update(User).where(User.id == user_id).values(last_login_at=at))


class SQLAlchemyAuthSessionRepository:
    """Persistence adapter for DB-driven refresh session lifecycle."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, user_id: str, refresh_jti: str, auth_method: AuthMethod, expires_at: datetime) -> AuthSession:
        session = AuthSession(
            user_id=user_id,
            refresh_jti=refresh_jti,
            auth_method=auth_method.value,
            expires_at=expires_at,
        )
        self.db.add(session)
        self.db.flush()
        return session

    def get_active_by_id(self, session_id: str) -> AuthSession | None:
        now = datetime.now(UTC)
        return self.db.scalar(
            select(AuthSession).where(
                AuthSession.id == session_id,
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > now,
            )
        )

    def get_active_by_refresh_jti(self, refresh_jti: str) -> AuthSession | None:
        now = datetime.now(UTC)
        return self.db.scalar(
            select(AuthSession).where(
                AuthSession.refresh_jti == refresh_jti,
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > now,
            )
        )

    def revoke(self, *, session_id: str, reason: str, replaced_by_jti: str | None = None) -> None:
        self.db.execute(
            update(AuthSession)
            .where(AuthSession.id == session_id, AuthSession.revoked_at.is_(None))
            .values(
                revoked_at=datetime.now(UTC),
                replaced_by_jti=replaced_by_jti,
                revoke_reason=reason,
            )
        )

    def revoke_all_for_user(self, *, user_id: str, reason: str) -> int:
        result = self.db.execute(
            update(AuthSession)
            .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC), revoke_reason=reason)
        )
        return result.rowcount or 0
