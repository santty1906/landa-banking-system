"""Database health checks used by startup and readiness endpoints."""

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger
from app.infrastructure.db.session import engine

logger = get_logger(__name__)


def check_database_connection() -> bool:
    """Return True when the database responds to a trivial query."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        logger.warning("Database health check failed", exc_info=True)
        return False
