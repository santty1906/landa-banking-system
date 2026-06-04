"""Version 1 API router composition.

Keeping each API version isolated makes future migrations to /api/v2 simpler.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.system import router as system_router

router = APIRouter()
router.include_router(system_router, tags=["system"])
