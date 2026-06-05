"""Use-case orchestration for face enrollment and facial login."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.interfaces.face_auth import AuthAuditRepository, EmbeddingCipher, FaceEmbeddingRepository
from app.domain.interfaces.face_recognition import FaceRecognitionService
from app.core.exceptions import AuthenticationError, InfrastructureError, ValidationAppError
from app.core.logging import get_logger
from app.infrastructure.security.jwt import create_access_token, create_refresh_token

logger = get_logger(__name__)


@dataclass(slots=True)
class FaceEnrollmentResult:
    """Response payload for successful face enrollment."""

    user_id: str
    model_name: str
    status: str = "enrolled"


@dataclass(slots=True)
class FaceLoginResult:
    """Response payload for successful face login."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class FaceAuthService:
    """Coordinates validation, embedding, encryption, persistence and auditing."""

    def __init__(
        self,
        *,
        face_recognition_service: FaceRecognitionService,
        embedding_repository: FaceEmbeddingRepository,
        audit_repository: AuthAuditRepository,
        embedding_cipher: EmbeddingCipher,
    ) -> None:
        self._face_recognition_service = face_recognition_service
        self._embedding_repository = embedding_repository
        self._audit_repository = audit_repository
        self._embedding_cipher = embedding_cipher

    def enroll_face(
        self,
        *,
        user_id: str,
        image_bytes: bytes,
        request_id: str,
        client_ip: str | None,
        user_agent: str | None,
    ) -> FaceEnrollmentResult:
        """Enroll a user face while keeping images ephemeral and embeddings encrypted."""
        try:
            quality = self._face_recognition_service.validate_image_quality(image_bytes)
            if not quality.is_valid:
                reason = quality.reason_code or "LOW_QUALITY_IMAGE"
                self._safe_audit(
                    method="face",
                    outcome="failure",
                    reason_code=reason,
                    request_id=request_id,
                    user_id=user_id,
                    client_ip=client_ip,
                    user_agent=user_agent,
                )
                raise ValidationAppError(
                    "Image does not meet minimum quality requirements",
                    details={"reason_code": reason},
                )

            embedding = self._face_recognition_service.generate_embedding(image_bytes)
            encrypted_payload = self._embedding_cipher.encrypt_embedding(embedding)

            self._embedding_repository.upsert_embedding(
                user_id=user_id,
                encrypted_embedding=encrypted_payload.ciphertext,
                encryption_metadata=encrypted_payload.metadata,
                model_name=self._face_recognition_service.model_name,
            )

            self._safe_audit(
                method="face",
                outcome="success",
                reason_code="FACE_ENROLLMENT_SUCCESS",
                request_id=request_id,
                user_id=user_id,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            return FaceEnrollmentResult(user_id=user_id, model_name=self._face_recognition_service.model_name)
        except ValidationAppError:
            raise
        except InfrastructureError:
            self._safe_audit(
                method="face",
                outcome="failure",
                reason_code="FACE_ENROLLMENT_ERROR",
                request_id=request_id,
                user_id=user_id,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            raise
        except Exception as exc:  # noqa: BLE001
            self._safe_audit(
                method="face",
                outcome="failure",
                reason_code="FACE_ENROLLMENT_ERROR",
                request_id=request_id,
                user_id=user_id,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            raise InfrastructureError("Face enrollment failed") from exc

    def login_with_face(
        self,
        *,
        user_id: str,
        image_bytes: bytes,
        request_id: str,
        client_ip: str | None,
        user_agent: str | None,
    ) -> FaceLoginResult:
        """Authenticate a user against an enrolled encrypted embedding."""
        stored_embedding = self._embedding_repository.get_embedding_by_user_id(user_id)
        if not stored_embedding:
            self._safe_audit(
                method="face",
                outcome="failure",
                reason_code="FACE_NOT_ENROLLED",
                request_id=request_id,
                user_id=user_id,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            raise AuthenticationError("Face authentication failed")

        quality = self._face_recognition_service.validate_image_quality(image_bytes)
        if not quality.is_valid:
            reason = quality.reason_code or "LOW_QUALITY_IMAGE"
            self._safe_audit(
                method="face",
                outcome="failure",
                reason_code=reason,
                request_id=request_id,
                user_id=user_id,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            raise AuthenticationError("Face authentication failed")

        try:
            candidate_embedding = self._face_recognition_service.generate_embedding(image_bytes)
            reference_embedding = self._embedding_cipher.decrypt_embedding(
                stored_embedding.encrypted_embedding,
                stored_embedding.encryption_metadata,
            )
            comparison = self._face_recognition_service.compare_embeddings(
                reference_embedding,
                candidate_embedding,
            )
        except InfrastructureError:
            self._safe_audit(
                method="face",
                outcome="failure",
                reason_code="FACE_LOGIN_ERROR",
                request_id=request_id,
                user_id=user_id,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            raise
        except Exception as exc:  # noqa: BLE001
            self._safe_audit(
                method="face",
                outcome="failure",
                reason_code="FACE_LOGIN_ERROR",
                request_id=request_id,
                user_id=user_id,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            raise InfrastructureError("Face authentication unavailable") from exc

        if not comparison.is_match:
            self._safe_audit(
                method="face",
                outcome="failure",
                reason_code="FACE_MISMATCH",
                request_id=request_id,
                user_id=user_id,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            raise AuthenticationError("Face authentication failed")

        access_token = create_access_token(subject=user_id)
        refresh_token = create_refresh_token(subject=user_id)
        self._safe_audit(
            method="face",
            outcome="success",
            reason_code="FACE_LOGIN_SUCCESS",
            request_id=request_id,
            user_id=user_id,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        return FaceLoginResult(access_token=access_token, refresh_token=refresh_token)

    def _safe_audit(
        self,
        *,
        method: str,
        outcome: str,
        reason_code: str,
        request_id: str,
        user_id: str | None,
        client_ip: str | None,
        user_agent: str | None,
    ) -> None:
        """Best-effort audit logging to keep auth flow resilient for MVP."""
        try:
            self._audit_repository.create_log(
                method=method,
                outcome=outcome,
                reason_code=reason_code,
                request_id=request_id,
                user_id=user_id,
                client_ip=client_ip,
                user_agent=user_agent,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to write authentication audit log",
                extra={"reason_code": reason_code},
                exc_info=exc,
            )
