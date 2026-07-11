def test_index_redirects_to_login(client):
    resp = client.get("/", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Sign in" in resp.data


def test_dashboard_redirects_anonymous(client):
    resp = client.get("/dashboard", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Please log in" in resp.data


def test_dashboard_shows_for_logged_user(logged_client):
    resp = logged_client.get("/dashboard")
    assert resp.status_code == 200
    assert b"Account Balance" in resp.data


def test_settings_redirects_anonymous(client):
    resp = client.get("/settings", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Please log in" in resp.data


def test_settings_page(logged_client):
    resp = logged_client.get("/settings")
    assert resp.status_code == 200
    assert b"Profile Settings" in resp.data


def test_settings_update_email(logged_client, app):
    with app.app_context():
        from app.models import User, db
        user = User.query.filter_by(username="testuser").first()
        old_email = user.email

    resp = logged_client.post("/settings", data={
        "email": "updated@example.com",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Email updated" in resp.data

    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        assert user.email == "updated@example.com"


def test_face_status_not_enrolled(logged_client):
    resp = logged_client.get("/api/face/status")
    assert resp.status_code == 200
    assert resp.json["enrolled"] is False


def test_face_verify_without_enrollment(logged_client):
    resp = logged_client.post("/api/face/verify", json={
        "image": "data:image/jpeg;base64,invalid",
    })
    assert resp.status_code == 401


def test_face_enroll_missing_images(logged_client):
    resp = logged_client.post("/api/face/enroll", json={})
    assert resp.status_code == 400
    assert "No images provided" in resp.json["error"]


def test_face_enroll_invalid_data(logged_client):
    resp = logged_client.post("/api/face/enroll", json={
        "images": {"frontal": "not-a-valid-image"},
    })
    assert resp.status_code == 400 or resp.status_code == 500


def test_protected_apis_require_login(client):
    for path in ["/api/face/status", "/api/face/enroll", "/api/face/verify"]:
        resp = client.post(path) if path != "/api/face/status" else client.get(path)
        assert resp.status_code == 302 or resp.status_code == 401


def test_face_check_user_not_found(client, app):
    with app.app_context():
        resp = client.get("/api/face/check-user?username=nonexistent")
        assert resp.json["enrolled"] is False


def test_face_check_user_empty(client):
    resp = client.get("/api/face/check-user?username=")
    assert resp.json["enrolled"] is False


def test_face_check_user_found_not_enrolled(client, registered_user):
    resp = client.get("/api/face/check-user?username=testuser")
    assert resp.json["enrolled"] is False


def test_face_login_verify_missing_data(client):
    resp = client.post("/api/face/login-verify", json={})
    assert resp.status_code == 400


def test_face_login_verify_no_username(client):
    resp = client.post("/api/face/login-verify", json={
        "image": "data:image/jpeg;base64,test",
        "username": "",
    })
    assert resp.status_code == 400


def test_face_login_verify_user_not_found(client):
    resp = client.post("/api/face/login-verify", json={
        "image": "data:image/jpeg;base64,test",
        "username": "nobody",
    })
    assert resp.status_code == 404


def test_face_login_verify_not_enrolled(client, registered_user):
    resp = client.post("/api/face/login-verify", json={
        "image": "data:image/jpeg;base64,test",
        "username": "testuser",
    })
    assert resp.status_code == 400
    assert "not enrolled" in resp.json["error"]


def test_offline_page(client):
    resp = client.get("/offline")
    assert resp.status_code == 200
    assert b"Offline" in resp.data or b"offline" in resp.data

def test_trusted_device_flow(client, app):
    with app.app_context():
        from app.models import User, db
        from app.security import hash_password

        user = User(
            username="trustuser",
            email="trust@example.com",
            password_hash=hash_password("Testpass123"),
            face_enrolled=True,
        )
        db.session.add(user)
        db.session.commit()

    with client:
        resp = client.get("/api/face/check-user?username=trustuser")
        assert resp.json["enrolled"] is False

        login_resp = client.post("/auth/login", data={
            "username": "trustuser",
            "password": "Testpass123",
        })
        assert login_resp.status_code == 302

        resp2 = client.get("/api/face/check-user?username=trustuser")
        assert resp2.json["enrolled"] is True


def test_face_login_verify_rejects_untrusted_device(client, app):
    with app.app_context():
        from app.models import User, db
        from app.security import hash_password

        user = User(
            username="untrusteduser",
            email="untrusted@example.com",
            password_hash=hash_password("Testpass123"),
            face_enrolled=True,
        )
        db.session.add(user)
        db.session.commit()

    resp = client.post("/api/face/login-verify", json={
        "username": "untrusteduser",
        "image": "data:image/jpeg;base64,test",
    })
    assert resp.status_code == 403

