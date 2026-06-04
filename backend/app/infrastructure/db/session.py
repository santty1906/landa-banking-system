"""Synchronous SQLAlchemy engine/session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Sync mode is intentionally chosen for readability and easier debugging in this MVP.
engine = create_engine(
    settings.sqlalchemy_database_uri,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)


def get_db() -> Session:
    """Provide one DB session per request and always close it safely."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
