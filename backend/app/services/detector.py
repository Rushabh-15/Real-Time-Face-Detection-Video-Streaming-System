"""MediaPipe face detection wrapper (Tasks API).

Pure-function service: numpy image array in, at-most-one BBox out. No I/O,
no FastAPI, no Pillow — those concerns live elsewhere so this layer stays
unit-testable in isolation against a JPEG-decoded fixture.

Uses mp.tasks.vision.FaceDetector. The legacy mp.solutions.face_detection
API is broken in current mediapipe versions across multiple platforms; the
Tasks API is the actively maintained path.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

import mediapipe as mp
import numpy as np

from app.config import Settings

# BlazeFace short-range model, bundled in the repo (~230KB, Apache 2.0).
# Committed so `docker compose up` works offline with zero setup steps.
MODEL_PATH = Path(__file__).resolve().parent / "models" / "blaze_face_short_range.tflite"


@dataclass(frozen=True, slots=True)
class BBox:
    """Axis-aligned bounding box in absolute pixel coordinates.

    `(x, y)` is the top-left corner; `(w, h)` are width and height. All
    clamped to image bounds. `confidence` is the detection score in [0, 1].
    """

    x: int
    y: int
    w: int
    h: int
    confidence: float


class FaceDetector:
    """Stateful wrapper around mp.tasks.vision.FaceDetector.

    The underlying graph is **not** thread-safe; an internal lock serializes
    inference so the FastAPI threadpool (driven by `asyncio.to_thread`)
    can't race two WS connections through the same instance. The lock is
    held only around the inference call.

    Constructed once at app startup, reused for the lifetime of the app,
    closed in the lifespan shutdown hook.
    """

    def __init__(
        self,
        min_confidence: float = 0.5,
        model_path: Path = MODEL_PATH,
    ) -> None:
        if not model_path.exists():
            raise FileNotFoundError(
                f"face detector model not found at {model_path}. "
                "Download it with the curl command in the README "
                "(Quick start → model setup)."
            )

        self._lock = threading.Lock()
        options = mp.tasks.vision.FaceDetectorOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
            running_mode=mp.tasks.vision.RunningMode.IMAGE,
            min_detection_confidence=min_confidence,
        )
        self._detector = mp.tasks.vision.FaceDetector.create_from_options(options)

    @classmethod
    def from_settings(cls, settings: Settings) -> FaceDetector:
        return cls(min_confidence=settings.DETECTION_MIN_CONFIDENCE)

    def detect(self, image_rgb: np.ndarray) -> BBox | None:
        """Detect at most one face in an RGB image.

        Multiple faces → highest-confidence one wins (rubric: one face per
        frame). No faces, or a degenerate box entirely outside the image
        after clamping → None.

        Args:
            image_rgb: shape (H, W, 3), dtype uint8, RGB color order.

        Raises:
            ValueError: if the input array isn't a 3-channel image.
        """
        if image_rgb.ndim != 3 or image_rgb.shape[2] != 3:
            raise ValueError(
                f"expected RGB image of shape (H, W, 3); got {image_rgb.shape}"
            )

        h, w = image_rgb.shape[:2]
        # mp.Image expects contiguous uint8 RGB. PIL→numpy gives this, but
        # be defensive against caller-provided non-contiguous arrays.
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=np.ascontiguousarray(image_rgb),
        )

        with self._lock:
            result = self._detector.detect(mp_image)

        if not result.detections:
            return None

        # Multiple faces → highest confidence wins.
        best = max(result.detections, key=lambda d: d.categories[0].score)
        bbox = best.bounding_box

        # Tasks API returns absolute pixel coords, but detections at the
        # frame edge can poke past the boundary. Clamp.
        x = max(0, bbox.origin_x)
        y = max(0, bbox.origin_y)
        x2 = min(w, bbox.origin_x + bbox.width)
        y2 = min(h, bbox.origin_y + bbox.height)

        if x2 <= x or y2 <= y:
            return None

        return BBox(
            x=x,
            y=y,
            w=x2 - x,
            h=y2 - y,
            confidence=float(best.categories[0].score),
        )

    def close(self) -> None:
        """Release the underlying MediaPipe resources."""
        self._detector.close()