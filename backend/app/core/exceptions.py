"""Structured exceptions and handlers for predictable API error responses."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger


class AppError(Exception):
    """Base application exception with stable error envelope fields."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str,
        status_code: int,
        details: dict | None = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(AppError):
    def __init__(self, message: str = "Authentication failed", *, details: dict | None = None) -> None:
        super().__init__(
            message,
            error_code="AUTH_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class InfrastructureError(AppError):
    def __init__(self, message: str = "Infrastructure unavailable", *, details: dict | None = None) -> None:
        super().__init__(
            message,
            error_code="INFRA_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


class ValidationAppError(AppError):
    def __init__(self, message: str = "Validation failed", *, details: dict | None = None) -> None:
        super().__init__(
            message,
            error_code="APP_VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


def _build_error_payload(request: Request, error_code: str, message: str, details: dict | None = None) -> dict:
    request_id = getattr(request.state, "request_id", "-")
    return {
        "error": {
            "code": error_code,
            "message": message,
            "details": details or {},
            "request_id": request_id,
        }
    }


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers in one place for maintainability."""

    logger = get_logger(__name__)

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        logger.warning("Application error: %s", exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=_build_error_payload(request, exc.error_code, exc.message, exc.details),
        )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        logger.warning("HTTP exception: %s", exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=_build_error_payload(request, "HTTP_ERROR", str(exc.detail)),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning("Validation error: %s", exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_build_error_payload(
                request,
                "VALIDATION_ERROR",
                "Request validation failed",
                {"errors": exc.errors()},
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unexpected error")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_build_error_payload(request, "INTERNAL_ERROR", "Internal server error"),
        )
