"""API schemas for /api/v1/roi.

Wire format for clients is intentionally close to the DB shape — flat
bbox columns rather than a nested object. Clients can compose
{x, y, w, h} client-side; nesting over JSON would add bytes and an
extra indirection for no gain at this scale.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoiRecord(BaseModel):
    """One persisted face detection.

    `from_attributes=True` lets the route do
    `RoiRecord.model_validate(orm_face_detection)` directly — no manual
    converter — because field names match the FaceDetection ORM columns.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    frame_timestamp: datetime
    bbox_x: int = Field(..., description="Top-left X (pixels)")
    bbox_y: int = Field(..., description="Top-left Y (pixels)")
    bbox_w: int = Field(..., description="Width (pixels)")
    bbox_h: int = Field(..., description="Height (pixels)")
    confidence: float = Field(..., ge=0.0, le=1.0)
    created_at: datetime


class RoiPage(BaseModel):
    """Paginated response for GET /api/v1/roi."""

    session_id: str
    items: list[RoiRecord]
    limit: int
    offset: int
    next_offset: int | None = Field(
        None,
        description="Offset for the next page; null when this is the last page.",
    )