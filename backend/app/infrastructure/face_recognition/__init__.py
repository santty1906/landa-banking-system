"""Face recognition infrastructure package behind adapter abstractions."""

from app.infrastructure.face_recognition.adapters import DeepFaceRecognitionAdapter, NullFaceRecognitionAdapter

__all__ = ["DeepFaceRecognitionAdapter", "NullFaceRecognitionAdapter"]
