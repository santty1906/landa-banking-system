from fastapi.testclient import TestClient

from app.core.exceptions import AppError
from app.main import create_app


def test_app_error_response_shape():
    app = create_app()

    @app.get("/raise-app-error")
    def raise_app_error():
        raise AppError("broken", error_code="BROKEN", status_code=418)

    client = TestClient(app)
    response = client.get("/raise-app-error")

    assert response.status_code == 418
    body = response.json()
    assert body["error"]["code"] == "BROKEN"
    assert body["error"]["message"] == "broken"
    assert "request_id" in body["error"]


def test_unexpected_error_response_shape():
    app = create_app()

    @app.get("/raise-unexpected")
    def raise_unexpected():
        raise RuntimeError("unexpected")

    client = TestClient(app)
    response = client.get("/raise-unexpected")

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
