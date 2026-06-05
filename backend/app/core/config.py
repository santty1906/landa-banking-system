"""Typed application settings loaded from environment variables.

Keeping all runtime config in one place makes the project easier to maintain,
especially for beginner/intermediate contributors.
"""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized, typed settings with beginner-friendly defaults."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_env: str = Field(default="development")
    app_name: str = Field(default="Landa Backend API")
    app_version: str = Field(default="0.1.0")
    api_v1_prefix: str = Field(default="/api/v1")

    postgres_host: str = Field(default="db")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="landa_db")
    postgres_user: str = Field(default="landa_user")
    postgres_password: str = Field(default="change_me")
    database_url: str | None = Field(default=None)

    jwt_secret_key: str = Field(default="change_this_secret")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_minutes: int = Field(default=1440)

    log_level: str = Field(default="INFO")
    log_format: str = Field(default="text")

    face_recognition_model: str = Field(default="Facenet512")
    face_recognition_detector_backend: str = Field(default="opencv")
    face_match_threshold: float = Field(default=0.35)
    face_image_max_size_bytes: int = Field(default=5_000_000)
    face_image_min_width: int = Field(default=120)
    face_image_min_height: int = Field(default=120)
    face_image_min_brightness: float = Field(default=35.0)
    face_image_min_laplacian_variance: float = Field(default=80.0)
    face_embedding_encryption_key: str = Field(default="change_this_face_embedding_key")
    face_embedding_key_version: str = Field(default="v1")


    @model_validator(mode="after")
    def validate_security_defaults(self) -> "Settings":
        """Block insecure default embedding key outside local development."""
        if self.app_env.lower() != "development" and self.face_embedding_encryption_key == "change_this_face_embedding_key":
            raise ValueError("FACE_EMBEDDING_ENCRYPTION_KEY must be changed outside development")
        return self

    @property
    def sqlalchemy_database_uri(self) -> str:
        """Build a sync SQLAlchemy URL unless an explicit DATABASE_URL is provided."""
        if self.database_url:
            return self.database_url
        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Cached settings prevent repeated env parsing across requests."""
    return Settings()
