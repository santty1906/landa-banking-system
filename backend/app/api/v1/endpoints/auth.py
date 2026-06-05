"""Authentication endpoints for registration, login, refresh, session, and logout."""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.v1.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshRequest,
    RegisterRequest,
    SessionResponse,
    TokenPairResponse,
)
from app.application.auth import AuthService
from app.domain.auth.entities import AuthContext
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPairResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> TokenPairResponse:
    service = AuthService(db)
    result = service.register_user(payload.email, payload.password)
    return TokenPairResponse.model_validate(result)


@router.post("/login", response_model=TokenPairResponse)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> TokenPairResponse:
    service = AuthService(db)
    result = service.login_user(payload.email, payload.password)
    return TokenPairResponse.model_validate(result)


@router.post("/refresh", response_model=TokenPairResponse)
def refresh(payload: RefreshRequest, db: Annotated[Session, Depends(get_db)]) -> TokenPairResponse:
    service = AuthService(db)
    result = service.refresh_tokens(refresh_token=payload.refresh_token)
    return TokenPairResponse.model_validate(result)


@router.get("/session", response_model=SessionResponse)
def read_session(current_user: Annotated[AuthContext, Depends(get_current_user)]) -> SessionResponse:
    return SessionResponse.model_validate(asdict(current_user))


@router.post("/logout", response_model=LogoutResponse)
def logout(
    payload: LogoutRequest,
    current_user: Annotated[AuthContext, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> LogoutResponse:
    service = AuthService(db)
    result = service.logout(auth_context=current_user, all_sessions=payload.all_sessions)
    return LogoutResponse.model_validate(result)
