"""Version 1 API router composition.

Keeping each API version isolated makes future migrations to /api/v2 simpler.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.auth_face import router as auth_face_router
from app.api.v1.endpoints.system import router as system_router

router = APIRouter()
router.include_router(system_router, tags=["system"])
router.include_router(auth_face_router, tags=["auth-face"])
router.include_router(auth_router)
