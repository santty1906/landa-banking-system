import pytest
from app.app import create_app
from app.models import User, db as _db
from app.config import Config


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    WTF_CSRF_ENABLED = False


@pytest.fixture
def app():
    app = create_app(TestConfig, database_uri="sqlite:///:memory:")
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    with app.app_context():
        yield _db


@pytest.fixture
def registered_user(app):
    with app.app_context():
        from app.security import hash_password

        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("testpass123"),
        )
        _db.session.add(user)
        _db.session.commit()
        return user


@pytest.fixture
def logged_client(client, registered_user):
    with client:
        client.post("/auth/login", data={
            "username": "testuser",
            "password": "testpass123",
        })
        yield client
