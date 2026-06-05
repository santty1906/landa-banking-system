"""SQLAlchemy repositories for facial auth persistence concerns."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.application.interfaces.face_auth import AuthAuditRepository, FaceEmbeddingRepository, StoredFaceEmbedding
from app.infrastructure.db.models.auth_audit_log import AuthAuditLog
from app.infrastructure.db.models.face_embedding import FaceEmbedding


class SqlAlchemyFaceEmbeddingRepository(FaceEmbeddingRepository):
    """Stores and retrieves encrypted face templates using SQLAlchemy."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def upsert_embedding(
        self,
        *,
        user_id: str,
        encrypted_embedding: str,
        encryption_metadata: dict[str, str],
        model_name: str,
    ) -> None:
        existing = self._db.get(FaceEmbedding, user_id)
        if existing:
            existing.encrypted_embedding = encrypted_embedding
            existing.encryption_metadata = encryption_metadata
            existing.model_name = model_name
        else:
            self._db.add(
                FaceEmbedding(
                    user_id=user_id,
                    encrypted_embedding=encrypted_embedding,
                    encryption_metadata=encryption_metadata,
                    model_name=model_name,
                )
            )
        self._db.commit()

    def get_embedding_by_user_id(self, user_id: str) -> StoredFaceEmbedding | None:
        entity = self._db.get(FaceEmbedding, user_id)
        if entity is None:
            return None
        return StoredFaceEmbedding(
            user_id=entity.user_id,
            encrypted_embedding=entity.encrypted_embedding,
            encryption_metadata=entity.encryption_metadata,
            model_name=entity.model_name,
        )


class SqlAlchemyAuthAuditRepository(AuthAuditRepository):
    """Persists authentication attempt events to the audit log table."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create_log(
        self,
        *,
        method: str,
        outcome: str,
        reason_code: str,
        request_id: str,
        user_id: str | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        self._db.add(
            AuthAuditLog(
                user_id=user_id,
                method=method,
                outcome=outcome,
                reason_code=reason_code,
                request_id=request_id,
                client_ip=client_ip,
                user_agent=user_agent,
            )
        )
        self._db.commit()
