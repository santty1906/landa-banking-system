"""Facial authentication endpoints for enrollment and login workflows."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from pydantic import BaseModel

from app.api.dependencies.face_auth import get_face_auth_service
from app.application.services.face_auth import FaceAuthService
from app.core.exceptions import ValidationAppError

router = APIRouter(prefix="/auth/face")


class FaceEnrollmentResponse(BaseModel):
    """Normalized response for successful face enrollment."""

    status: str = "enrolled"
    user_id: str
    model_name: str


class FaceLoginResponse(BaseModel):
    """Token envelope returned after successful face authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


@router.post("/enroll", response_model=FaceEnrollmentResponse)
async def enroll_face(
    request: Request,
    user_id: Annotated[str, Form(min_length=1, max_length=64)],
    image: Annotated[UploadFile, File(...)],
    service: Annotated[FaceAuthService, Depends(get_face_auth_service)],
) -> FaceEnrollmentResponse:
    """Enroll a user's face without persisting raw images on disk."""
    if image.content_type is None or not image.content_type.startswith("image/"):
        raise ValidationAppError("Image file is required")

    image_bytes = await image.read()
    if not image_bytes:
        raise ValidationAppError("Image file is required")

    result = service.enroll_face(
        user_id=user_id,
        image_bytes=image_bytes,
        request_id=_get_request_id(request),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return FaceEnrollmentResponse(status=result.status, user_id=result.user_id, model_name=result.model_name)


@router.post("/login", response_model=FaceLoginResponse)
async def login_with_face(
    request: Request,
    user_id: Annotated[str, Form(min_length=1, max_length=64)],
    image: Annotated[UploadFile, File(...)],
    service: Annotated[FaceAuthService, Depends(get_face_auth_service)],
) -> FaceLoginResponse:
    """Authenticate using face comparison against enrolled encrypted embedding."""
    if image.content_type is None or not image.content_type.startswith("image/"):
        raise ValidationAppError("Image file is required")

    image_bytes = await image.read()
    if not image_bytes:
        raise ValidationAppError("Image file is required")

    result = service.login_with_face(
        user_id=user_id,
        image_bytes=image_bytes,
        request_id=_get_request_id(request),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return FaceLoginResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type=result.token_type,
    )
