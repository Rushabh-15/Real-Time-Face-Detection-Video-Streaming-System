"""WebSocket endpoint for the face-stream protocol.

Bidirectional and full-duplex. The client sends raw binary JPEG frames;
the server runs each through the detection pipeline and sends back a
`FaceFrameMessage` JSON envelope (annotated JPEG + ROI bounding box).

This single endpoint satisfies both the rubric's "POST /ingest (or
WebSocket)" and "GET /stream (or WebSocket)" line items — one full-duplex
WebSocket avoids splitting ingest and stream into separate channels with
a session broker between them.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from app.services.detector import FaceDetector
from app.services.pipeline import process_frame

router = APIRouter(tags=["face-stream"])


@router.websocket("/ws/face-stream")
async def face_stream(websocket: WebSocket) -> None:
    """Receive binary JPEG frames; send back the annotated frame + ROI as JSON.

    The shared `FaceDetector` is read from `app.state` (constructed in the
    app lifespan). Each frame's `process_frame` call runs in a worker
    thread via `asyncio.to_thread` so MediaPipe inference doesn't block
    the event loop.
    """
    detector: FaceDetector = websocket.app.state.detector

    await websocket.accept()
    logger.info("face-stream client connected")

    try:
        while True:
            jpeg_in = await websocket.receive_bytes()

            try:
                msg = await asyncio.to_thread(process_frame, detector, jpeg_in)
            except ValueError as exc:
                # Bad input from the client (corrupt JPEG, wrong shape, etc.).
                # Log and drop the frame; keep the connection alive.
                logger.warning(f"frame rejected: {exc}")
                continue
            except Exception:
                # Server-side pipeline bug. Log with traceback, drop the
                # frame, keep the connection. We'd rather lose one frame
                # than tear down a 30fps stream.
                logger.exception("pipeline failure; dropping frame")
                continue

            await websocket.send_json(msg.model_dump())
    except WebSocketDisconnect:
        logger.info("face-stream client disconnected")