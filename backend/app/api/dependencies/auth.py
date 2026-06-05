"""Authentication dependencies kept in the API layer only."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.application.auth import AuthService
from app.core.config import get_settings
from app.domain.auth.entities import AuthContext
from app.infrastructure.db.session import get_db

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> AuthContext:
    """Validate access token and attach DB-backed auth context to request state."""
    auth_context = AuthService(db).validate_session(access_token=token)
    request.state.auth_context = auth_context
    return auth_context
