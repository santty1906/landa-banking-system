"""Application entrypoint and startup wiring for the FastAPI service."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import RequestIDMiddleware, get_logger, setup_logging
from app.infrastructure.db.health import check_database_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run lightweight startup checks without blocking the whole app."""
    logger = get_logger(__name__)
    db_ready = check_database_connection()
    if db_ready:
        logger.info("Database connectivity check passed during startup")
    else:
        logger.warning("Database connectivity check failed during startup; readiness will be degraded")
    yield


def create_app() -> FastAPI:
    """App factory keeps startup predictable and testing simple."""
    settings = get_settings()
    setup_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        description="Backend foundation only. Business logic intentionally pending.",
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(RequestIDMiddleware)
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
