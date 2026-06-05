import pytest
from app.core.config import Settings, get_settings

pytestmark = pytest.mark.unit


def test_settings_build_database_uri(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "landa_test")
    monkeypatch.setenv("POSTGRES_USER", "landa")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")

    get_settings.cache_clear()
    settings = Settings()

    assert settings.sqlalchemy_database_uri.startswith("postgresql+psycopg://")
    assert "localhost:5432/landa_test" in settings.sqlalchemy_database_uri


def test_database_url_override(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///tmp/custom.db")

    get_settings.cache_clear()
    settings = Settings()

    assert settings.sqlalchemy_database_uri == "sqlite:///tmp/custom.db"
