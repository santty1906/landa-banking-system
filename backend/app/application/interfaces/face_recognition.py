"""Application-level protocol aliases for clean architecture readability."""

from app.domain.interfaces.face_recognition import (
    FaceComparisonResult,
    FaceQualityResult,
    FaceRecognitionService,
)

__all__ = ["FaceRecognitionService", "FaceQualityResult", "FaceComparisonResult"]
