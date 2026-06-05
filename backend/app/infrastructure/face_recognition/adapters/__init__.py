"""Face recognition adapter exports."""

from app.infrastructure.face_recognition.adapters.base import DeepFaceRecognitionAdapter, NullFaceRecognitionAdapter

__all__ = ["DeepFaceRecognitionAdapter", "NullFaceRecognitionAdapter"]
