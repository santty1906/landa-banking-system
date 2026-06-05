import pytest
from sqlalchemy.orm import Session

from app.application.auth import AuthService
from app.core.exceptions import AuthenticationError
from app.infrastructure.security.jwt import decode_token


def test_register_returns_access_and_refresh_tokens(db_session: Session) -> None:
    service = AuthService(db_session)

    result = service.register_user("student1@example.com", "securePassword123")

    assert "access_token" in result
    assert "refresh_token" in result
    access_payload = decode_token(result["access_token"])
    refresh_payload = decode_token(result["refresh_token"])
    assert access_payload.token_type.value == "access"
    assert refresh_payload.token_type.value == "refresh"


def test_login_invalid_credentials_returns_generic_auth_error(db_session: Session) -> None:
    service = AuthService(db_session)
    service.register_user("student2@example.com", "securePassword123")

    with pytest.raises(AuthenticationError, match="Invalid credentials"):
        service.login_user("student2@example.com", "wrongPassword")



def test_refresh_rotation_invalidates_previous_refresh_token(db_session: Session) -> None:
    service = AuthService(db_session)
    tokens = service.register_user("student3@example.com", "securePassword123")

    rotated_tokens = service.refresh_tokens(refresh_token=tokens["refresh_token"])

    with pytest.raises(AuthenticationError, match="Invalid or revoked refresh token"):
        service.refresh_tokens(refresh_token=tokens["refresh_token"])

    assert rotated_tokens["refresh_token"] != tokens["refresh_token"]
