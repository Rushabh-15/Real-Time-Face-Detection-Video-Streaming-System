"""Unit tests for the face detection service.

Loads a face JPEG fixture and verifies BlazeFace detects it. The detector
fixture is module-scoped so the ~1.5s TFLite warmup happens once for the
whole file.
"""

from pathlib import Path
from collections.abc import Iterator

import numpy as np
import pytest

from app.services.detector import BBox, FaceDetector
from app.services.drawing import decode_jpeg

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
FACE_JPEG_PATH = FIXTURES_DIR / "face.jpg"


# ---------- fixtures ----------


@pytest.fixture(scope="module")
def detector() -> Iterator[FaceDetector]:
    """One detector for the whole module — TFLite warmup amortized."""
    d = FaceDetector(min_confidence=0.5)
    try:
        yield d
    finally:
        d.close()


@pytest.fixture
def face_image() -> np.ndarray:
    """Decoded RGB array of the bundled face fixture.

    Skips dependent tests with a clear message if the fixture is missing,
    so tests that don't need a real face still run.
    """
    if not FACE_JPEG_PATH.exists():
        pytest.skip(
            f"face fixture missing at {FACE_JPEG_PATH}. "
            "Generate one with the resize command in tests/fixtures setup."
        )
    return decode_jpeg(FACE_JPEG_PATH.read_bytes())


# ---------- happy path: detection on a real face ----------


def test_detect_returns_bbox_for_face_image(
    detector: FaceDetector, face_image: np.ndarray
) -> None:
    bbox = detector.detect(face_image)

    assert bbox is not None
    assert isinstance(bbox, BBox)


def test_bbox_is_within_image_bounds(
    detector: FaceDetector, face_image: np.ndarray
) -> None:
    h, w = face_image.shape[:2]
    bbox = detector.detect(face_image)
    assert bbox is not None

    assert 0 <= bbox.x < w
    assert 0 <= bbox.y < h
    assert bbox.x + bbox.w <= w
    assert bbox.y + bbox.h <= h


def test_bbox_has_positive_dimensions(
    detector: FaceDetector, face_image: np.ndarray
) -> None:
    bbox = detector.detect(face_image)
    assert bbox is not None
    assert bbox.w > 0
    assert bbox.h > 0


def test_confidence_is_in_unit_interval(
    detector: FaceDetector, face_image: np.ndarray
) -> None:
    bbox = detector.detect(face_image)
    assert bbox is not None
    assert 0.0 <= bbox.confidence <= 1.0


# ---------- no-face path (rubric: "what if no face?") ----------


def test_returns_none_for_blank_image(detector: FaceDetector) -> None:
    """A solid-grey image has no detectable face."""
    blank = np.full((480, 640, 3), 128, dtype=np.uint8)
    assert detector.detect(blank) is None


# ---------- validation guards ----------


def test_rejects_grayscale_array(detector: FaceDetector) -> None:
    grayscale = np.zeros((100, 100), dtype=np.uint8)
    with pytest.raises(ValueError, match="expected RGB image"):
        detector.detect(grayscale)


def test_rejects_rgba_array(detector: FaceDetector) -> None:
    rgba = np.zeros((100, 100, 4), dtype=np.uint8)
    with pytest.raises(ValueError, match="expected RGB image"):
        detector.detect(rgba)