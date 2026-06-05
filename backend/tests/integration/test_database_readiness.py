from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.db.health import check_database_connection
from app.main import create_app

pytestmark = pytest.mark.integration


def test_database_healthcheck_uses_real_connection():
    assert check_database_connection() is True


def test_readiness_reports_ready_when_database_is_available():
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/health/readiness")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["services"]["database"] == "up"
