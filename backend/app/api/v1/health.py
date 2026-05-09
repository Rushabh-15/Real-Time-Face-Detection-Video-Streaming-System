"""Liveness check endpoint.

Reports that the service process is up. Does *not* check downstream
dependencies (DB, model). A separate /readiness endpoint will do that
once we have dependencies to check.
"""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness check",
    description=(
        "Returns 200 if the service process is up. Does not check downstream "
        "dependencies (database, model availability) — those will live on "
        "/readiness when added."
    ),
)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="face-detect-stream",
        version="0.1.0",
    )