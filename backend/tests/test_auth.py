def test_login_page(client):
    resp = client.get("/auth/login")
    assert resp.status_code == 200
    assert b"LANDA Bank" in resp.data


def test_register_page(client):
    resp = client.get("/auth/register")
    assert resp.status_code == 200
    assert b"Create Account" in resp.data


def test_successful_registration(client, db):
    resp = client.post("/auth/register", data={
        "username": "newuser",
        "email": "new@example.com",
        "password": "password123",
        "confirm_password": "password123",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Registration successful" in resp.data


def test_duplicate_username_registration(client, db, registered_user):
    resp = client.post("/auth/register", data={
        "username": "testuser",
        "email": "other@example.com",
        "password": "password123",
        "confirm_password": "password123",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"already taken" in resp.data


def test_password_mismatch(client):
    resp = client.post("/auth/register", data={
        "username": "user1",
        "email": "user1@example.com",
        "password": "password123",
        "confirm_password": "different",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"do not match" in resp.data


def test_successful_login(client, registered_user):
    resp = client.post("/auth/login", data={
        "username": "testuser",
        "password": "testpass123",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Welcome back" in resp.data


def test_failed_login(client):
    resp = client.post("/auth/login", data={
        "username": "nonexistent",
        "password": "wrongpassword",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Invalid username or password" in resp.data


def test_logout(logged_client):
    resp = logged_client.get("/auth/logout", follow_redirects=True)
    assert resp.status_code == 200
    assert b"logged out" in resp.data


def test_empty_fields_login(client):
    resp = client.post("/auth/login", data={
        "username": "",
        "password": "",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"fill in all fields" in resp.data


def test_short_password_rejected(client):
    resp = client.post("/auth/register", data={
        "username": "user2",
        "email": "user2@example.com",
        "password": "ab",
        "confirm_password": "ab",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"at least 8 characters" in resp.data


def test_password_without_digits_rejected(client):
    resp = client.post("/auth/register", data={
        "username": "user3",
        "email": "user3@example.com",
        "password": "onlyletters",
        "confirm_password": "onlyletters",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"letters and numbers" in resp.data

def test_duplicate_email_registration(client, db, registered_user):
    resp = client.post("/auth/register", data={
        "username": "anotheruser",
        "email": "test@example.com",
        "password": "password123",
        "confirm_password": "password123",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"already registered" in resp.data

