"""Dependency wiring for facial authentication use cases."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.services.face_auth import FaceAuthService
from app.infrastructure.db.session import get_db
from app.infrastructure.face_recognition.adapters import DeepFaceRecognitionAdapter
from app.infrastructure.repositories import SqlAlchemyAuthAuditRepository, SqlAlchemyFaceEmbeddingRepository
from app.infrastructure.security.embedding_crypto import FernetEmbeddingCipher


def get_face_auth_service(db: Annotated[Session, Depends(get_db)]) -> FaceAuthService:
    """Build per-request FaceAuthService with infrastructure-backed dependencies."""
    return FaceAuthService(
        face_recognition_service=DeepFaceRecognitionAdapter(),
        embedding_repository=SqlAlchemyFaceEmbeddingRepository(db),
        audit_repository=SqlAlchemyAuthAuditRepository(db),
        embedding_cipher=FernetEmbeddingCipher(),
    )
