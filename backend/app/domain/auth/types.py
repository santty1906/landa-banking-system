"""Authentication domain types for extensible factor-based auth flows."""

from __future__ import annotations

from enum import Enum


class AuthMethod(str, Enum):
    """Authentication methods supported now and planned for future expansions."""

    PASSWORD = "password"
    FACE = "face"
    MFA = "mfa"
