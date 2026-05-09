"""Shared pytest fixtures for the backend test suite."""

from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pytest

from app.services.detector import FaceDetector
from app.services.drawing import decode_jpeg

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
FACE_JPEG_PATH = FIXTURES_DIR / "face.jpg"


@pytest.fixture
def rgb_image() -> np.ndarray:
    """A 100x100 RGB image with a solid mid-green tint.

    Suitable for codec round-trip and drawing tests where the content
    doesn't matter — only shape, dtype, and structural integrity.
    """
    arr = np.zeros((100, 100, 3), dtype=np.uint8)
    arr[:, :, 1] = 128
    return arr


@pytest.fixture(scope="session")
def detector() -> Iterator[FaceDetector]:
    """One FaceDetector for the whole test session.

    Session-scoped so the ~1.5s TFLite model warmup happens once across
    all test files (detector tests, pipeline tests, future API tests).
    """
    d = FaceDetector(min_confidence=0.5)
    try:
        yield d
    finally:
        d.close()


@pytest.fixture
def face_jpeg_bytes() -> bytes:
    """Raw bytes of the bundled face fixture.

    Skips dependent tests with a clear message if the fixture is missing,
    so unrelated tests still run.
    """
    if not FACE_JPEG_PATH.exists():
        pytest.skip(
            f"face fixture missing at {FACE_JPEG_PATH}. "
            "See the tests/fixtures setup in the README."
        )
    return FACE_JPEG_PATH.read_bytes()


@pytest.fixture
def face_image(face_jpeg_bytes: bytes) -> np.ndarray:
    """Decoded RGB array of the bundled face fixture.

    Depends on `face_jpeg_bytes` so the missing-fixture skip cascades —
    one place to check existence, all dependent tests skip cleanly.
    """
    return decode_jpeg(face_jpeg_bytes)