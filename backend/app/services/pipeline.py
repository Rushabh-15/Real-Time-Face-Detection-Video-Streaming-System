"""Frame processing pipeline.

Pure orchestration: JPEG bytes in → annotated JPEG + ROI envelope out.
Composes the detector and drawing services into a single per-frame
operation. Stateless — the long-lived `FaceDetector` is passed in by the
caller (typically the WS handler).
"""

from __future__ import annotations

import base64

from app.schemas.ws import ROI, FaceFrameMessage
from app.services.detector import BBox, FaceDetector
from app.services.drawing import decode_jpeg, draw_bbox, encode_jpeg


def process_frame(detector: FaceDetector, jpeg_in: bytes) -> FaceFrameMessage:
    """Run a single frame through the full pipeline.

    decode → detect → draw → encode → envelope.

    Args:
        detector: a long-lived `FaceDetector` instance.
        jpeg_in:  JPEG-encoded frame bytes from the client.

    Returns:
        A `FaceFrameMessage` with the annotated frame base64-encoded and
        the detected `ROI` (or `None` if no face was found).

    Raises:
        ValueError: if the bytes don't decode as a 3-channel image.
        PIL.UnidentifiedImageError: if the bytes aren't a recognized image format.
    """
    image = decode_jpeg(jpeg_in)
    bbox = detector.detect(image)
    annotated = draw_bbox(image, bbox)
    jpeg_out = encode_jpeg(annotated)

    return FaceFrameMessage(
        frame=base64.b64encode(jpeg_out).decode("ascii"),
        roi=_bbox_to_roi(bbox),
    )


def _bbox_to_roi(bbox: BBox | None) -> ROI | None:
    """Convert internal `BBox` to wire-format `ROI`.

    Lives in the pipeline (not on `BBox`) to keep `detector.py` independent
    of the wire schema — services don't know about Pydantic models.
    """
    if bbox is None:
        return None
    return ROI(
        x=bbox.x,
        y=bbox.y,
        w=bbox.w,
        h=bbox.h,
        confidence=bbox.confidence,
    )