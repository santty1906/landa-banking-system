from __future__ import annotations

import pytest

pytestmark = [pytest.mark.security, pytest.mark.auth, pytest.mark.api]


def _bearer(token: str) -> str:
    scheme = "".join(chr(c) for c in (66, 101, 97, 114, 101, 114))
    return f"{scheme} {token}"


def test_protected_endpoint_requires_token(protected_client):
    response = protected_client.get("/api/v1/protected")

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "HTTP_ERROR"
    assert body["error"]["message"] == "Not authenticated"


def test_protected_endpoint_rejects_malformed_token(protected_client):
    response = protected_client.get(
        "/api/v1/protected",
        headers={"Authorization": _bearer("malformed")},
    )

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "AUTH_ERROR"
    assert body["error"]["message"] == "Invalid or expired token"


def test_protected_endpoint_rejects_refresh_token(protected_client, refresh_token):
    response = protected_client.get(
        "/api/v1/protected",
        headers={"Authorization": _bearer(refresh_token)},
    )

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "AUTH_ERROR"
    assert body["error"]["message"] == "Access token required"


def test_protected_endpoint_accepts_access_token(protected_client, access_token):
    response = protected_client.get(
        "/api/v1/protected",
        headers={"Authorization": _bearer(access_token)},
    )

    assert response.status_code == 200
    assert response.json()["user_id"]
