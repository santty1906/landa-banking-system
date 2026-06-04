"""Typed application settings loaded from environment variables.

Keeping all runtime config in one place makes the project easier to maintain,
especially for beginner/intermediate contributors.
"""

from functools import lru_cache

from pydantic import Field
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
