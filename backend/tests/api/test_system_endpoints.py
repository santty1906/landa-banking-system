from fastapi.testclient import TestClient

from app.main import create_app


def test_liveness_endpoint_returns_alive():
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/health/liveness")

    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_readiness_endpoint_ready(monkeypatch):
    monkeypatch.setattr("app.api.v1.endpoints.system.check_database_connection", lambda: True)
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/health/readiness")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["services"]["database"] == "up"


def test_readiness_endpoint_degraded(monkeypatch):
    monkeypatch.setattr("app.api.v1.endpoints.system.check_database_connection", lambda: False)
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/health/readiness")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["services"]["database"] == "down"
    assert body["diagnostics"]["http_status_policy"]["ready"] == 200
    assert body["diagnostics"]["http_status_policy"]["degraded"] == 503
