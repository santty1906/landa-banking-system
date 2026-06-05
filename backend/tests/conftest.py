from __future__ import annotations

from typing import Annotated

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_user
from app.core.config import get_settings
from app.infrastructure.security.jwt import create_access_token, create_refresh_token
from app.main import create_app


@pytest.fixture(autouse=True)
def isolate_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def app():
    return create_app()


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
def access_token(configured_jwt_env):
    return create_access_token("student_1")


@pytest.fixture
def refresh_token(configured_jwt_env):
    return create_refresh_token("student_1")


@pytest.fixture
def protected_client(configured_jwt_env):
    app = create_app()

    @app.get("/api/v1/protected")
    def protected(current_user: Annotated[dict[str, str], Depends(get_current_user)]) -> dict[str, str]:
        return {"user_id": current_user["user_id"]}

    with TestClient(app) as test_client:
        yield test_client
