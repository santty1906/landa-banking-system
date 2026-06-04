from app.core.config import get_settings
from app.infrastructure.security.jwt import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
)


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
