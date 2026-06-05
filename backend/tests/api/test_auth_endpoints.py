from fastapi.testclient import TestClient


def test_register_returns_token_pair(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "demo1@example.com", "password": "securePassword123"},
    )

    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_refresh_token_rotation_prevents_replay(client: TestClient) -> None:
    register = client.post(
        "/api/v1/auth/register",
        json={"email": "demo2@example.com", "password": "securePassword123"},
    ).json()

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": register["refresh_token"]},
    )
    assert refresh_response.status_code == 200

    replay_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": register["refresh_token"]},
    )

    assert replay_response.status_code == 401
    assert replay_response.json()["error"]["code"] == "AUTH_ERROR"


def test_session_endpoint_returns_lightweight_metadata(client: TestClient) -> None:
    register = client.post(
        "/api/v1/auth/register",
        json={"email": "demo3@example.com", "password": "securePassword123"},
    ).json()

    response = client.get(
        "/api/v1/auth/session",
        headers={"Authorization": "Bearer " + register["access_token"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "user_id",
        "email",
        "is_active",
        "auth_method",
        "session_created_at",
        "token_expiration",
        "last_login_at",
    }


def test_logout_current_session_only_by_default(client: TestClient) -> None:
    register = client.post(
        "/api/v1/auth/register",
        json={"email": "demo4@example.com", "password": "securePassword123"},
    ).json()

    response = client.post(
        "/api/v1/auth/logout",
        json={},
        headers={"Authorization": "Bearer " + register["access_token"]},
    )

    assert response.status_code == 200
    assert response.json()["revoked_sessions"] == 1


def test_logout_all_sessions_option_revokes_multiple_sessions(client: TestClient) -> None:
    register = client.post(
        "/api/v1/auth/register",
        json={"email": "demo5@example.com", "password": "securePassword123"},
    ).json()

    second_login = client.post(
        "/api/v1/auth/login",
        json={"email": "demo5@example.com", "password": "securePassword123"},
    )
    assert second_login.status_code == 200

    logout_all = client.post(
        "/api/v1/auth/logout",
        json={"all_sessions": True},
        headers={"Authorization": "Bearer " + register["access_token"]},
    )

    assert logout_all.status_code == 200
    assert logout_all.json()["revoked_sessions"] >= 2
