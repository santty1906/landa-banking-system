"""Infrastructure adapters for face recognition providers."""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.exceptions import InfrastructureError
from app.core.logging import get_logger
from app.domain.interfaces.face_recognition import FaceComparisonResult, FaceQualityResult, FaceRecognitionService

logger = get_logger(__name__)


class DeepFaceRecognitionAdapter(FaceRecognitionService):
    """DeepFace-backed adapter encapsulating provider-specific implementation details."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def model_name(self) -> str:
        return self._settings.face_recognition_model

    def validate_image_quality(self, image_bytes: bytes) -> FaceQualityResult:
        """Validate size, resolution, blur, brightness and single-face detection."""
        if len(image_bytes) > self._settings.face_image_max_size_bytes:
            return FaceQualityResult(
                is_valid=False,
                reason_code="IMAGE_TOO_LARGE",
                message="Image exceeds maximum upload size",
            )

        np, cv2 = self._load_cv_modules()
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            return FaceQualityResult(
                is_valid=False,
                reason_code="INVALID_IMAGE",
                message="Unable to decode image",
            )

        height, width = image.shape[:2]
        if width < self._settings.face_image_min_width or height < self._settings.face_image_min_height:
            return FaceQualityResult(
                is_valid=False,
                reason_code="LOW_RESOLUTION",
                message="Image resolution is too low",
            )

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        brightness = float(gray.mean())
        if brightness < self._settings.face_image_min_brightness:
            return FaceQualityResult(
                is_valid=False,
                reason_code="LOW_BRIGHTNESS",
                message="Image brightness is too low",
            )

        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if blur_score < self._settings.face_image_min_laplacian_variance:
            return FaceQualityResult(
                is_valid=False,
                reason_code="BLURRY_IMAGE",
                message="Image appears too blurry",
            )

        face_count = self._count_faces(image_bytes)
        if face_count == 0:
            return FaceQualityResult(
                is_valid=False,
                reason_code="NO_FACE_DETECTED",
                message="No face detected",
            )
        if face_count > 1:
            return FaceQualityResult(
                is_valid=False,
                reason_code="MULTIPLE_FACES_DETECTED",
                message="Exactly one face is required",
            )

        return FaceQualityResult(is_valid=True)

    def generate_embedding(self, image_bytes: bytes) -> list[float]:
        """Generate an embedding for the provided image using DeepFace represent."""
        deepface_module = self._load_deepface_module()
        image_path = self._write_temp_image(image_bytes)
        try:
            representations = deepface_module.represent(
                img_path=image_path,
                model_name=self._settings.face_recognition_model,
                detector_backend=self._settings.face_recognition_detector_backend,
                enforce_detection=True,
            )
            if not representations:
                raise InfrastructureError("Face embedding generation failed")

            first_result = representations[0]
            embedding = first_result.get("embedding") if isinstance(first_result, dict) else None
            if not embedding:
                raise InfrastructureError("Face embedding generation failed")
            return [float(value) for value in embedding]
        except InfrastructureError:
            raise
        except ValueError as exc:
            raise InfrastructureError("Face embedding generation failed") from exc
        except RuntimeError as exc:
            raise InfrastructureError("Face embedding generation failed") from exc
        finally:
            Path(image_path).unlink(missing_ok=True)

    def compare_embeddings(
        self,
        reference_embedding: list[float],
        candidate_embedding: list[float],
    ) -> FaceComparisonResult:
        """Compare embeddings using cosine distance and configured threshold."""
        np, _ = self._load_cv_modules()

        reference = np.array(reference_embedding, dtype=float)
        candidate = np.array(candidate_embedding, dtype=float)

        ref_norm = np.linalg.norm(reference)
        cand_norm = np.linalg.norm(candidate)
        if ref_norm == 0.0 or cand_norm == 0.0:
            raise InfrastructureError("Invalid embedding vectors for comparison")

        cosine_distance = float(1 - np.dot(reference, candidate) / (ref_norm * cand_norm))
        threshold = self._settings.face_match_threshold
        return FaceComparisonResult(
            is_match=cosine_distance <= threshold,
            distance=cosine_distance,
            threshold=threshold,
        )

    def _count_faces(self, image_bytes: bytes) -> int:
        deepface_module = self._load_deepface_module()
        image_path = self._write_temp_image(image_bytes)
        try:
            faces = deepface_module.extract_faces(
                img_path=image_path,
                detector_backend=self._settings.face_recognition_detector_backend,
                enforce_detection=False,
            )
            return len(faces)
        except ValueError:
            return 0
        except RuntimeError as exc:
            logger.warning("Face detection runtime error", exc_info=exc)
            return 0
        finally:
            Path(image_path).unlink(missing_ok=True)

    @staticmethod
    def _write_temp_image(image_bytes: bytes) -> str:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_file.write(image_bytes)
            return temp_file.name

    @staticmethod
    def _load_deepface_module():
        try:
            from deepface import DeepFace
        except (ImportError, ModuleNotFoundError) as exc:
            raise InfrastructureError("DeepFace provider unavailable") from exc
        return DeepFace

    @staticmethod
    def _load_cv_modules():
        try:
            import cv2
            import numpy as np
        except (ImportError, ModuleNotFoundError) as exc:
            raise InfrastructureError("Image processing dependencies unavailable") from exc
        return np, cv2


class NullFaceRecognitionAdapter(FaceRecognitionService):
    """Safe default adapter until a concrete provider is integrated."""

    @property
    def model_name(self) -> str:
        return "null"

    def validate_image_quality(self, image_bytes: bytes) -> FaceQualityResult:
        raise NotImplementedError("Face recognition adapter is not implemented yet")

    def generate_embedding(self, image_bytes: bytes) -> list[float]:
        raise NotImplementedError("Face recognition adapter is not implemented yet")

    def compare_embeddings(
        self,
        reference_embedding: list[float],
        candidate_embedding: list[float],
    ) -> FaceComparisonResult:
        raise NotImplementedError("Face recognition adapter is not implemented yet")
