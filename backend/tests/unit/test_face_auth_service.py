from dataclasses import dataclass

import pytest

from app.application.interfaces.face_auth import EncryptedEmbeddingPayload, StoredFaceEmbedding
from app.application.services.face_auth import FaceAuthService
from app.core.exceptions import AuthenticationError, ValidationAppError
from app.domain.interfaces.face_recognition import FaceComparisonResult, FaceQualityResult


@dataclass
class FakeFaceRecognitionService:
    quality_result: FaceQualityResult
    comparison_result: FaceComparisonResult
    embedding: list[float]
    model_name: str = "fake-model"

    def validate_image_quality(self, image_bytes: bytes) -> FaceQualityResult:
        del image_bytes
        return self.quality_result

    def generate_embedding(self, image_bytes: bytes) -> list[float]:
        del image_bytes
        return self.embedding

    def compare_embeddings(self, reference_embedding: list[float], candidate_embedding: list[float]) -> FaceComparisonResult:
        del reference_embedding, candidate_embedding
        return self.comparison_result


class FakeEmbeddingRepository:
    def __init__(self, stored: StoredFaceEmbedding | None = None):
        self.stored = stored
        self.upsert_calls = []

    def upsert_embedding(self, *, user_id: str, encrypted_embedding: str, encryption_metadata: dict[str, str], model_name: str):
        self.upsert_calls.append(
            {
                "user_id": user_id,
                "encrypted_embedding": encrypted_embedding,
                "encryption_metadata": encryption_metadata,
                "model_name": model_name,
            }
        )

    def get_embedding_by_user_id(self, user_id: str) -> StoredFaceEmbedding | None:
        del user_id
        return self.stored


class FakeAuditRepository:
    def __init__(self):
        self.logs = []

    def create_log(self, **kwargs):
        self.logs.append(kwargs)


class FakeEmbeddingCipher:
    def encrypt_embedding(self, embedding: list[float]) -> EncryptedEmbeddingPayload:
        del embedding
        return EncryptedEmbeddingPayload(ciphertext="enc", metadata={"key_version": "v1"})

    def decrypt_embedding(self, ciphertext: str, metadata: dict[str, str]) -> list[float]:
        del ciphertext, metadata
        return [0.1, 0.2, 0.3]


def test_enroll_face_happy_path(monkeypatch):
    monkeypatch.setattr("app.application.services.face_auth.create_access_token", lambda subject: f"access-{subject}")
    monkeypatch.setattr("app.application.services.face_auth.create_refresh_token", lambda subject: f"refresh-{subject}")

    service = FaceAuthService(
        face_recognition_service=FakeFaceRecognitionService(
            quality_result=FaceQualityResult(is_valid=True),
            comparison_result=FaceComparisonResult(is_match=True, distance=0.1, threshold=0.35),
            embedding=[0.1, 0.2, 0.3],
        ),
        embedding_repository=FakeEmbeddingRepository(),
        audit_repository=FakeAuditRepository(),
        embedding_cipher=FakeEmbeddingCipher(),
    )

    result = service.enroll_face(
        user_id="student-1",
        image_bytes=b"fake-image",
        request_id="req-1",
        client_ip="127.0.0.1",
        user_agent="pytest",
    )

    assert result.status == "enrolled"
    assert result.user_id == "student-1"


def test_enroll_face_rejects_low_quality():
    audit_repo = FakeAuditRepository()
    service = FaceAuthService(
        face_recognition_service=FakeFaceRecognitionService(
            quality_result=FaceQualityResult(is_valid=False, reason_code="LOW_RESOLUTION"),
            comparison_result=FaceComparisonResult(is_match=True, distance=0.1, threshold=0.35),
            embedding=[0.1, 0.2, 0.3],
        ),
        embedding_repository=FakeEmbeddingRepository(),
        audit_repository=audit_repo,
        embedding_cipher=FakeEmbeddingCipher(),
    )

    with pytest.raises(ValidationAppError):
        service.enroll_face(
            user_id="student-1",
            image_bytes=b"fake-image",
            request_id="req-1",
            client_ip=None,
            user_agent=None,
        )

    assert audit_repo.logs[-1]["reason_code"] == "LOW_RESOLUTION"


def test_login_with_face_success(monkeypatch):
    monkeypatch.setattr("app.application.services.face_auth.create_access_token", lambda subject: f"access-{subject}")
    monkeypatch.setattr("app.application.services.face_auth.create_refresh_token", lambda subject: f"refresh-{subject}")

    service = FaceAuthService(
        face_recognition_service=FakeFaceRecognitionService(
            quality_result=FaceQualityResult(is_valid=True),
            comparison_result=FaceComparisonResult(is_match=True, distance=0.1, threshold=0.35),
            embedding=[0.1, 0.2, 0.3],
        ),
        embedding_repository=FakeEmbeddingRepository(
            StoredFaceEmbedding(
                user_id="student-1",
                encrypted_embedding="enc",
                encryption_metadata={"key_version": "v1"},
                model_name="fake-model",
            )
        ),
        audit_repository=FakeAuditRepository(),
        embedding_cipher=FakeEmbeddingCipher(),
    )

    result = service.login_with_face(
        user_id="student-1",
        image_bytes=b"fake-image",
        request_id="req-2",
        client_ip="127.0.0.1",
        user_agent="pytest",
    )

    assert result.access_token == "access-student-1"
    assert result.refresh_token == "refresh-student-1"


def test_login_with_face_rejects_mismatch(monkeypatch):
    monkeypatch.setattr("app.application.services.face_auth.create_access_token", lambda subject: f"access-{subject}")
    monkeypatch.setattr("app.application.services.face_auth.create_refresh_token", lambda subject: f"refresh-{subject}")

    service = FaceAuthService(
        face_recognition_service=FakeFaceRecognitionService(
            quality_result=FaceQualityResult(is_valid=True),
            comparison_result=FaceComparisonResult(is_match=False, distance=0.9, threshold=0.35),
            embedding=[0.1, 0.2, 0.3],
        ),
        embedding_repository=FakeEmbeddingRepository(
            StoredFaceEmbedding(
                user_id="student-1",
                encrypted_embedding="enc",
                encryption_metadata={"key_version": "v1"},
                model_name="fake-model",
            )
        ),
        audit_repository=FakeAuditRepository(),
        embedding_cipher=FakeEmbeddingCipher(),
    )

    with pytest.raises(AuthenticationError):
        service.login_with_face(
            user_id="student-1",
            image_bytes=b"fake-image",
            request_id="req-2",
            client_ip="127.0.0.1",
            user_agent="pytest",
        )
