"""Domain layer: core business entities and contracts (no framework coupling)."""

from app.domain.auth import AuthContext, AuthMethod

__all__ = ["AuthContext", "AuthMethod"]
