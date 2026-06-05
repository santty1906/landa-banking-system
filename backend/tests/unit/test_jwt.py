import pytest
from app.core.config import get_settings
from app.infrastructure.security.jwt import (
    TokenType,
    build_refresh_rotation_claims,
    create_access_token,
    create_refresh_token,
    decode_token,
)

pytestmark = [pytest.mark.unit, pytest.mark.auth, pytest.mark.security]


def test_create_and_decode_access_token(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret")
    get_settings.cache_clear()

    token = create_access_token("student_1")
    payload = decode_token(token)

    assert payload.sub == "student_1"
    assert payload.token_type == TokenType.ACCESS


def test_create_and_decode_refresh_token(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret")
    get_settings.cache_clear()

    token = create_refresh_token("student_1")
    payload = decode_token(token)

    assert payload.sub == "student_1"
    assert payload.token_type == TokenType.REFRESH


def test_build_refresh_rotation_claims():
    claims = build_refresh_rotation_claims("previous-token-id")

    assert claims == {"previous_jti": "previous-token-id"}
