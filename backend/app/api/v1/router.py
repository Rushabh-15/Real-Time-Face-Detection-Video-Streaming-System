"""Aggregate v1 API router.

Per-resource routers are included here. Endpoints land under the prefix
configured by `Settings.API_V1_PREFIX` (default `/api/v1`).
"""

from fastapi import APIRouter

from app.api.v1 import face_stream, health

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(face_stream.router)

# Per-resource routers are included as they're added:
#   from app.api.v1 import health
#   api_router.include_router(health.router)