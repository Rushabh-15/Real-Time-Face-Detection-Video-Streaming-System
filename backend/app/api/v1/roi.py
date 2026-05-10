"""GET /api/v1/roi — paginated list of persisted face detections."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories.face_detection import FaceDetectionRepository
from app.schemas.roi import RoiPage, RoiRecord

router = APIRouter(tags=["roi"])

# Hard cap on a single page so a malicious / buggy client can't ask for
# 100k rows in one shot. 500 is generous for the rubric's use case.
_MAX_PAGE_SIZE = 500


@router.get(
    "/roi",
    response_model=RoiPage,
    summary="List ROI bounding boxes for a session",
    description=(
        "Returns face detections persisted by the WebSocket pipeline, "
        "filtered by `session_id` and optionally a `since` timestamp. "
        "Results are ordered ASC by `frame_timestamp` so clients can "
        "resume by passing the last seen timestamp as the next `since`. "
        "Use `limit`/`offset` for offset-based pagination."
    ),
)
async def list_roi(
    session_id: Annotated[
        str,
        Query(
            min_length=1,
            max_length=64,
            description="Session id used by the WS client when streaming frames.",
        ),
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
    since: Annotated[
        datetime | None,
        Query(description="Return detections strictly after this timestamp (ISO-8601)."),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=_MAX_PAGE_SIZE)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> RoiPage:
    repo = FaceDetectionRepository(session)
    rows = await repo.list_by_session(
        session_id, since=since, limit=limit, offset=offset
    )
    items = [RoiRecord.model_validate(r) for r in rows]
    # `next_offset` is null when we returned fewer than `limit` items —
    # that's the unambiguous end-of-results signal for the client.
    next_offset = offset + limit if len(items) == limit else None
    return RoiPage(
        session_id=session_id,
        items=items,
        limit=limit,
        offset=offset,
        next_offset=next_offset,
    )