from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies.auth import get_current_user
from app.application.auth import AuthService
from app.core.config import get_settings
from app.infrastructure.db.base import Base
from app.infrastructure.db.session import get_db
from app.main import create_app


@pytest.fixture(autouse=True)
def isolate_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def sqlite_session_factory() -> Generator[sessionmaker, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from app.infrastructure.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)
    try:
        yield factory
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def db_session(sqlite_session_factory: sessionmaker) -> Generator[Session, None, None]:
    session = sqlite_session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def app(sqlite_session_factory: sessionmaker):
    fastapi_app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        db = sqlite_session_factory()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    try:
        yield fastapi_app
    finally:
        fastapi_app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def configured_jwt_env(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    get_settings.cache_clear()


@pytest.fixture
def issued_tokens(db_session: Session, configured_jwt_env) -> dict[str, str]:
    service = AuthService(db_session)
    raw_secret = "test-pass-123"
    return service.register_user("student_1@example.com", raw_secret)


@pytest.fixture
def access_token(issued_tokens):
    return issued_tokens["access_token"]


@pytest.fixture
def refresh_token(issued_tokens):
    return issued_tokens["refresh_token"]


@pytest.fixture
def protected_client(app):
    @app.get("/api/v1/protected")
    def protected(current_user: Annotated[object, Depends(get_current_user)]) -> dict[str, str]:
        return {"user_id": str(current_user.user_id)}

    with TestClient(app) as test_client:
        yield test_client
