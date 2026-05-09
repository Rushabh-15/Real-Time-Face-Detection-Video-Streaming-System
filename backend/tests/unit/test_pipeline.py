"""Unit tests for the frame processing pipeline.

The pipeline composes detector + drawing + base64 + envelope into one
operation. Tests use the shared session-scoped detector and the face
fixture from conftest.
"""

import base64

import numpy as np
import pytest

from app.schemas.ws import FaceFrameMessage
from app.services.detector import FaceDetector
from app.services.drawing import decode_jpeg, encode_jpeg
from app.services.pipeline import process_frame


# ---------- happy path: face fixture ----------


def test_returns_message_with_roi_for_face_frame(
    detector: FaceDetector, face_jpeg_bytes: bytes
) -> None:
    msg = process_frame(detector, face_jpeg_bytes)

    assert isinstance(msg, FaceFrameMessage)
    assert msg.roi is not None
    assert msg.roi.confidence > 0


# ---------- no-face path ----------


def test_returns_message_with_null_roi_for_blank_frame(
    detector: FaceDetector,
) -> None:
    blank = np.full((480, 640, 3), 128, dtype=np.uint8)
    blank_jpeg = encode_jpeg(blank)

    msg = process_frame(detector, blank_jpeg)

    assert msg.roi is None
    # Even with no face, the pipeline still produces a re-encoded JPEG.
    assert msg.frame
    assert isinstance(msg.frame, str)


# ---------- frame round-trip ----------


def test_frame_field_roundtrips_to_jpeg(
    detector: FaceDetector, face_jpeg_bytes: bytes
) -> None:
    """msg.frame is base64(JPEG); decoding it should yield a valid RGB image."""
    msg = process_frame(detector, face_jpeg_bytes)

    decoded_bytes = base64.b64decode(msg.frame)
    decoded_image = decode_jpeg(decoded_bytes)

    assert decoded_image.ndim == 3
    assert decoded_image.shape[2] == 3
    assert decoded_image.dtype == np.uint8


# ---------- BBox → ROI faithfulness ----------


def test_roi_fields_match_detector_output(
    detector: FaceDetector,
    face_jpeg_bytes: bytes,
    face_image: np.ndarray,
) -> None:
    """The ROI on the wire faithfully reflects the detector's BBox.

    Runs the detector twice (once directly, once via the pipeline) on the
    same face. Detector is deterministic, so values should match exactly.
    """
    bbox = detector.detect(face_image)
    assert bbox is not None  # sanity: fixture must contain a face

    msg = process_frame(detector, face_jpeg_bytes)
    assert msg.roi is not None

    assert msg.roi.x == bbox.x
    assert msg.roi.y == bbox.y
    assert msg.roi.w == bbox.w
    assert msg.roi.h == bbox.h
    assert msg.roi.confidence == bbox.confidence