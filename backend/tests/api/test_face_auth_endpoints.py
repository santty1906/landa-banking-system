from dataclasses import dataclass

from fastapi.testclient import TestClient

from app.api.dependencies.face_auth import get_face_auth_service
from app.application.services.face_auth import FaceEnrollmentResult, FaceLoginResult
from app.main import create_app


@dataclass
class FakeFaceAuthService:
    def enroll_face(self, **kwargs):
        del kwargs
        return FaceEnrollmentResult(user_id="student-1", model_name="fake-model")

    def login_with_face(self, **kwargs):
        del kwargs
        return FaceLoginResult(access_token="access", refresh_token="refresh")


def test_enroll_face_endpoint_success():
    app = create_app()
    app.dependency_overrides[get_face_auth_service] = lambda: FakeFaceAuthService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/face/enroll",
        data={"user_id": "student-1"},
        files={"image": ("face.jpg", b"fake-image-bytes", "image/jpeg")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "enrolled"
    assert body["user_id"] == "student-1"


def test_login_face_endpoint_success():
    app = create_app()
    app.dependency_overrides[get_face_auth_service] = lambda: FakeFaceAuthService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/face/login",
        data={"user_id": "student-1"},
        files={"image": ("face.jpg", b"fake-image-bytes", "image/jpeg")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] == "access"
    assert body["refresh_token"] == "refresh"


def test_face_endpoint_rejects_non_image_file():
    app = create_app()
    app.dependency_overrides[get_face_auth_service] = lambda: FakeFaceAuthService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/face/enroll",
        data={"user_id": "student-1"},
        files={"image": ("face.txt", b"not-image", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "APP_VALIDATION_ERROR"
