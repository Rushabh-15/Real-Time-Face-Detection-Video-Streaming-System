"""Write-behind worker for ROI persistence.

The WS handler runs at ~15-30 fps. Doing per-frame INSERTs inline would:
  (a) gate frame latency on DB latency (1-5ms minimum, more on contention),
  (b) own a session per WS connection (lifecycle pain) or churn sessions
      every frame (pool exhaustion).

Instead the WS handler calls `enqueue(payload)` — a non-blocking sync
call that drops to an asyncio.Queue. A single background task drains
the queue, batches up to N rows per commit or every T seconds (whichever
first), and runs the insert outside the WS hot path.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict, dataclass
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.repositories.face_detection import FaceDetectionRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class FaceDetectionPayload:
    """Wire format from WS handler to writer.

    Maps 1:1 to FaceDetection columns minus server-assigned (id, created_at).
    Frozen + slots: cheap to construct, immutable, can't be mutated mid-flight
    by a consumer.
    """

    session_id: str
    frame_timestamp: datetime
    bbox_x: int
    bbox_y: int
    bbox_w: int
    bbox_h: int
    confidence: float


class RoiWriter:
    """Singleton-ish write-behind worker.

    Constructed once at module import. main.py's lifespan calls
    start()/stop(). The WS handler imports the module-level `roi_writer`
    and calls enqueue(). No other public API.
    """

    def __init__(
        self,
        *,
        max_queue_size: int = 1000,
        batch_size: int = 50,
        batch_timeout_s: float = 1.0,
    ) -> None:
        # asyncio.Queue is loop-agnostic in Python 3.10+ until first awaited,
        # so constructing at import time is safe.
        self._queue: asyncio.Queue[FaceDetectionPayload] = asyncio.Queue(
            maxsize=max_queue_size
        )
        self._batch_size = batch_size
        self._batch_timeout_s = batch_timeout_s
        self._task: asyncio.Task[None] | None = None
        self._dropped = 0

    @property
    def dropped_count(self) -> int:
        """Cumulative payloads dropped due to queue overflow. Surfaced by /healthz later."""
        return self._dropped

    @property
    def queue_depth(self) -> int:
        """Current queue depth — useful for ops dashboards."""
        return self._queue.qsize()

    def enqueue(self, payload: FaceDetectionPayload) -> bool:
        """Non-blocking. Returns False if the queue was full and the item was dropped.

        WS hot path calls this; it MUST NOT await or raise. Failure mode is
        a dropped row, never a stalled video pipeline.
        """
        try:
            self._queue.put_nowait(payload)
            return True
        except asyncio.QueueFull:
            self._dropped += 1
            # Throttle: 1, 100, 200, 300… so sustained overflow doesn't flood logs.
            if self._dropped == 1 or self._dropped % 100 == 0:
                logger.warning(
                    "roi_writer queue full; %d payloads dropped cumulative",
                    self._dropped,
                )
            return False

    async def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._run(), name="roi-writer")
        logger.info("roi_writer started")

    async def stop(self) -> None:
        """Cancel the worker, then best-effort flush whatever's still queued."""
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
        await self._flush_remaining()
        logger.info(
            "roi_writer stopped (cumulative dropped=%d, final queue depth=%d)",
            self._dropped,
            self._queue.qsize(),
        )

    async def _run(self) -> None:
        """Main loop. Drains the queue in batches forever until cancelled."""
        while True:
            batch = await self._collect_batch()
            if batch:
                await self._write_batch(batch)

    async def _collect_batch(self) -> list[FaceDetectionPayload]:
        """Block on the first item up to batch_timeout_s, then opportunistically
        grab up to batch_size more without blocking. Returns [] on timeout
        (no items arrived) so the loop can re-check cancellation."""
        try:
            first = await asyncio.wait_for(
                self._queue.get(), timeout=self._batch_timeout_s
            )
        except asyncio.TimeoutError:
            return []

        batch = [first]
        while len(batch) < self._batch_size:
            try:
                batch.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        return batch

    async def _write_batch(self, batch: list[FaceDetectionPayload]) -> None:
        rows = [asdict(p) for p in batch]
        async with SessionLocal() as session:
            try:
                repo = FaceDetectionRepository(session)
                await repo.bulk_insert(rows)
                await session.commit()
            except SQLAlchemyError as exc:
                # Don't propagate — that would kill the worker task. Rollback,
                # log, drop the batch, keep draining. Transient DB blips don't
                # permanently break persistence.
                await session.rollback()
                logger.error(
                    "roi_writer batch failed (%d rows dropped): %s",
                    len(batch),
                    exc,
                    exc_info=False,
                )

    async def _flush_remaining(self) -> None:
        """Best-effort drain after the main task is stopped. Called from stop()."""
        remaining: list[FaceDetectionPayload] = []
        while True:
            try:
                remaining.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        if remaining:
            await self._write_batch(remaining)


# Module-level singleton. Defaults are reasonable for 30fps × a handful
# of sessions. Promote max_queue_size / batch_size / batch_timeout_s to
# Settings if the take-home stretches into production tuning.
roi_writer = RoiWriter()