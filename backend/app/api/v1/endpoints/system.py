"""System endpoints for service liveness and readiness diagnostics."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.infrastructure.db.health import check_database_connection

router = APIRouter()


@router.get("/health/liveness")
def liveness_check() -> dict:
    """Liveness: confirms the API process is up."""
    return {"status": "alive", "services": {"api": "up"}}


@router.get("/health/readiness")
def readiness_check() -> dict:
    """Readiness: reports degraded mode when database is unavailable."""
    db_ready = check_database_connection()

    if db_ready:
        return {
            "status": "ready",
            "services": {
                "api": "up",
                "database": "up",
            },
        }

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "degraded",
            "services": {
                "api": "up",
                "database": "down",
            },
            "message": "Database unavailable. Running in degraded mode.",
            "diagnostics": {
                "http_status_policy": {
                    "ready": status.HTTP_200_OK,
                    "degraded": status.HTTP_503_SERVICE_UNAVAILABLE,
                }
            },
        },
    )
