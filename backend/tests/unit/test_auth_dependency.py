from __future__ import annotations

import pytest
from jose import jwt
from starlette.requests import Request

from app.api.dependencies.auth import get_current_user
from app.application.auth import AuthService
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.infrastructure.security.jwt import TokenType, create_refresh_token

pytestmark = [pytest.mark.unit, pytest.mark.auth, pytest.mark.security]


def _request() -> Request:
    return Request({"type": "http", "headers": []})


def test_get_current_user_accepts_access_token(db_session, configured_jwt_env):
    token = AuthService(db_session).register_user("student_1@example.com", "test-pass-123")["access_token"]
    user = get_current_user(_request(), token, db_session)

    assert user.user_id
    assert user.email == "student_1@example.com"


def test_get_current_user_rejects_refresh_token(db_session, configured_jwt_env):
    token = create_refresh_token("student_1")

    with pytest.raises(AuthenticationError, match="Access token required"):
        get_current_user(_request(), token, db_session)


def test_get_current_user_rejects_missing_subject(db_session, configured_jwt_env):
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
        get_current_user(_request(), valid_token_without_subject, db_session)


def test_get_current_user_rejects_malformed_token(db_session):
    with pytest.raises(AuthenticationError, match="Invalid or expired token"):
        get_current_user(_request(), "this-is-not-a-jwt", db_session)
