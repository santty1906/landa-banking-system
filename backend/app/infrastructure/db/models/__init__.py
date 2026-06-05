"""Model registry for Alembic autogeneration."""

from app.infrastructure.db.models.auth_audit_log import AuthAuditLog
from app.infrastructure.db.models.face_embedding import FaceEmbedding

__all__ = ["AuthAuditLog", "FaceEmbedding"]
