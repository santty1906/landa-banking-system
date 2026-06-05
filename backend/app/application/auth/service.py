"""Authentication application service orchestrating auth use-cases."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError, AuthenticationError
from app.core.logging import get_logger
from app.domain.auth.entities import AuthContext
from app.domain.auth.types import AuthMethod
from app.infrastructure.repositories.auth import SQLAlchemyAuthSessionRepository, SQLAlchemyUserRepository
from app.infrastructure.security.jwt import (
    TokenType,
    build_refresh_rotation_claims,
    create_access_token,
    create_refresh_token,
    decode_token,
    token_expiration_datetime,
)
from app.infrastructure.security.password import PasswordHasher

logger = get_logger(__name__)


class AuthService:
    """Authentication use-cases for registration, login, refresh, and logout."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.users = SQLAlchemyUserRepository(db)
        self.sessions = SQLAlchemyAuthSessionRepository(db)
        self.hasher = PasswordHasher()

    def register_user(self, email: str, password: str) -> dict:
        existing = self.users.get_by_email(email)
        if existing:
            raise AppError(
                "Email is already registered",
                error_code="AUTH_EMAIL_EXISTS",
                status_code=409,
                details={"field": "email"},
            )

        user = self.users.create(email=email, password_hash=self.hasher.hash_password(password), is_active=True)
        now = datetime.now(UTC)
        self.users.update_last_login(user_id=user.id, at=now)
        tokens = self._issue_session_tokens(user_id=user.id, email=user.email, auth_method=AuthMethod.PASSWORD)
        self.db.commit()
        logger.info("event=auth_register_success user_id=%s email=%s", user.id, user.email)
        return self._sanitize_token_response(tokens)

    def login_user(self, email: str, password: str) -> dict:
        user = self.users.get_by_email(email)
        if not user or not self.hasher.verify_password(password, user.password_hash):
            logger.info("event=auth_login_failed reason=invalid_credentials email=%s", email)
            raise AuthenticationError("Invalid credentials")

        if not user.is_active:
            raise AuthenticationError("Account is inactive")

        now = datetime.now(UTC)
        self.users.update_last_login(user_id=user.id, at=now)
        tokens = self._issue_session_tokens(user_id=user.id, email=user.email, auth_method=AuthMethod.PASSWORD)
        self.db.commit()
        logger.info("event=auth_login_success user_id=%s", user.id)
        return self._sanitize_token_response(tokens)

    def refresh_tokens(self, *, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if payload.token_type != TokenType.REFRESH:
            raise AuthenticationError("Refresh token required")
        if not payload.sub:
            raise AuthenticationError("Token subject is missing")

        session = self.sessions.get_active_by_refresh_jti(payload.jti)
        if not session:
            logger.info("event=auth_refresh_failed reason=session_not_active")
            raise AuthenticationError("Invalid or revoked refresh token")

        if session.user_id != payload.sub:
            raise AuthenticationError("Invalid token subject")

        user = self.users.get_by_id(payload.sub)
        if not user or not user.is_active:
            raise AuthenticationError("Account is inactive")

        new_tokens = self._issue_session_tokens(
            user_id=user.id,
            email=user.email,
            auth_method=AuthMethod(session.auth_method),
            previous_jti=session.refresh_jti,
        )
        self.sessions.revoke(
            session_id=session.id,
            reason="refresh_rotation",
            replaced_by_jti=new_tokens["refresh_jti"],
        )
        self.db.commit()
        logger.info("event=auth_refresh_success user_id=%s", user.id)
        return self._sanitize_token_response(new_tokens)

    def validate_session(self, *, access_token: str) -> AuthContext:
        payload = decode_token(access_token)
        if payload.token_type != TokenType.ACCESS:
            raise AuthenticationError("Access token required")
        if not payload.sub:
            raise AuthenticationError("Token subject is missing")
        if not payload.sid:
            raise AuthenticationError("Session claim is missing")

        session = self.sessions.get_active_by_id(payload.sid)
        if not session:
            raise AuthenticationError("Session is no longer active")

        user = self.users.get_by_id(payload.sub)
        if not user or not user.is_active:
            raise AuthenticationError("Account is inactive")

        return AuthContext(
            user_id=user.id,
            email=user.email,
            is_active=user.is_active,
            auth_method=AuthMethod(session.auth_method),
            session_id=session.id,
            session_created_at=session.created_at,
            token_expiration=token_expiration_datetime(payload.exp),
            last_login_at=user.last_login_at,
        )

    def logout(self, *, auth_context: AuthContext, all_sessions: bool = False) -> dict[str, int]:
        if all_sessions:
            revoked_count = self.sessions.revoke_all_for_user(user_id=auth_context.user_id, reason="logout_all")
            logger.info("event=auth_logout_all user_id=%s revoked=%s", auth_context.user_id, revoked_count)
        else:
            self.sessions.revoke(session_id=auth_context.session_id, reason="logout_current")
            revoked_count = 1
            logger.info("event=auth_logout user_id=%s session_id=%s", auth_context.user_id, auth_context.session_id)

        self.db.commit()
        return {"revoked_sessions": revoked_count}

    def _issue_session_tokens(
        self,
        *,
        user_id: str,
        email: str,
        auth_method: AuthMethod,
        previous_jti: str | None = None,
    ) -> dict:
        refresh_token = create_refresh_token(
            subject=user_id,
            additional_claims=build_refresh_rotation_claims(previous_jti),
        )
        refresh_payload = decode_token(refresh_token)
        refresh_expires_at = token_expiration_datetime(refresh_payload.exp)
        session = self.sessions.create(
            user_id=user_id,
            refresh_jti=refresh_payload.jti,
            auth_method=auth_method,
            expires_at=refresh_expires_at,
        )
        access_token = create_access_token(
            subject=user_id,
            additional_claims={"sid": session.id, "email": email, "auth_method": auth_method.value},
        )
        access_payload = decode_token(access_token)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": max(0, access_payload.exp - int(datetime.now(UTC).timestamp())),
            "refresh_expires_in": max(0, refresh_payload.exp - int(datetime.now(UTC).timestamp())),
            "refresh_jti": refresh_payload.jti,
        }

    @staticmethod
    def _sanitize_token_response(tokens: dict) -> dict:
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
            "expires_in": tokens["expires_in"],
            "refresh_expires_in": tokens["refresh_expires_in"],
        }
