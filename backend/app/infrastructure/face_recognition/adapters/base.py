"""Infrastructure adapter placeholder for future facial recognition integration."""

from app.domain.interfaces.face_recognition import FaceRecognitionService


class NullFaceRecognitionAdapter(FaceRecognitionService):
    """Safe default adapter until a concrete provider is integrated."""

    def verify_faces(self, reference_image_path: str, candidate_image_path: str) -> bool:
        raise NotImplementedError("Face recognition adapter is not implemented yet")
