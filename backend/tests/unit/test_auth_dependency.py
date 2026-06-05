from __future__ import annotations

import pytest
from jose import jwt

from app.api.dependencies.auth import get_current_user
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.infrastructure.security.jwt import TokenType, create_access_token, create_refresh_token

pytestmark = [pytest.mark.unit, pytest.mark.auth, pytest.mark.security]


def test_get_current_user_accepts_access_token(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret")
    get_settings.cache_clear()

    token = create_access_token("student_1")
    user = get_current_user(token)

    assert user == {"user_id": "student_1"}


def test_get_current_user_rejects_refresh_token(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret")
    get_settings.cache_clear()

    token = create_refresh_token("student_1")

    with pytest.raises(AuthenticationError, match="Access token required"):
        get_current_user(token)


def test_get_current_user_rejects_missing_subject(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret")
    get_settings.cache_clear()
    settings = get_settings()

    valid_token_without_subject = jwt.encode(
        {
            "token_type": TokenType.ACCESS.value,
            "iat": 1710000000,
            "exp": 2710000000,
            "jti": "test-jti",
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(AuthenticationError, match="Token subject is missing"):
        get_current_user(valid_token_without_subject)


def test_get_current_user_rejects_malformed_token():
    with pytest.raises(AuthenticationError, match="Invalid or expired token"):
        get_current_user("this-is-not-a-jwt")
