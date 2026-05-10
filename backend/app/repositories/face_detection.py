"""Repository for face_detections table.

All SQL touching FaceDetection lives here. Service layer asks the
repository; nothing else writes raw SQLAlchemy queries.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FaceDetection


class FaceDetectionRepository:
    """Thin wrapper around AsyncSession for FaceDetection persistence.

    Session is owned by the caller; this class never commits. The caller
    decides when a transaction boundary is — typically the write-behind
    worker for inserts and a request-scoped dep for reads. That split is
    why we don't use a UnitOfWork here.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_insert(self, rows: Sequence[Mapping[str, object]]) -> None:
        """Insert N rows in one round trip.

        `rows` is a sequence of mappings whose keys match FaceDetection
        columns minus server-assigned ones (id, created_at). Uses Core
        insert (not ORM `add_all`) to skip per-instance overhead — this
        is on the worker hot path.
        """
        if not rows:
            return
        await self._session.execute(insert(FaceDetection), list(rows))

    async def list_by_session(
        self,
        session_id: str,
        *,
        since: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FaceDetection]:
        """Read for /api/v1/roi. Hits the (session_id, frame_timestamp) index."""
        stmt = (
            select(FaceDetection)
            .where(FaceDetection.session_id == session_id)
            .order_by(FaceDetection.frame_timestamp.asc())
            .limit(limit)
            .offset(offset)
        )
        if since is not None:
            stmt = stmt.where(FaceDetection.frame_timestamp > since)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())