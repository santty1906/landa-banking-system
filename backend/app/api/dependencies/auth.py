"""Authentication dependencies kept in the API layer only."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.infrastructure.security.jwt import TokenType, decode_token

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict[str, str]:
    """Placeholder auth dependency; user lookup will be added with business logic."""
    payload = decode_token(token)
    if payload.token_type != TokenType.ACCESS:
        raise AuthenticationError("Access token required")

    if not payload.sub:
        raise AuthenticationError("Token subject is missing")

    return {"user_id": payload.sub}
