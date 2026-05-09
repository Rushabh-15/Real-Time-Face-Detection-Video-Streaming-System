"""Pydantic schemas for the face-stream WebSocket protocol.

Inbound (client → server): raw binary JPEG frames. No schema — the protocol
is "bytes in," and a 33% base64 tax on the upstream path would be wasteful.

Outbound (server → client): JSON envelope with an annotated frame and the
detected ROI. Schema lives here so the WS handler, the pipeline service,
and the tests all bind to the same wire contract.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ROI(BaseModel):
    """Region of interest: an axis-aligned face bounding box.

    Field bounds (`ge=0`, `gt=0`, confidence in [0, 1]) are a safety net
    behind the detector's own clamping. If a future detector regression
    produces a degenerate box, Pydantic raises before the client sees it.
    """

    x: int = Field(ge=0, description="Top-left x in pixels")
    y: int = Field(ge=0, description="Top-left y in pixels")
    w: int = Field(gt=0, description="Width in pixels")
    h: int = Field(gt=0, description="Height in pixels")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Detection confidence in [0, 1]",
    )


class FaceFrameMessage(BaseModel):
    """Server → client message sent once per inbound frame.

    `frame` is the annotated JPEG re-encoded after drawing, base64-encoded
    as ASCII (no data-URI prefix). `roi` is null when no face was detected
    in the frame — clients should treat that as "show the frame as-is."
    """

    frame: str = Field(
        description="Annotated JPEG, base64-encoded (no data URI prefix)"
    )
    roi: ROI | None = Field(
        default=None,
        description="Detected face ROI; null when no face is detected",
    )