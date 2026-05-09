"""Unit tests for the drawing service.

Pure-function tests: synthetic numpy inputs, deterministic outputs. No
fixtures from disk, no network, no model loading.
"""

from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from app.services.detector import BBox
from app.services.drawing import decode_jpeg, draw_bbox, encode_jpeg


# ---------- encode / decode ----------


def test_encode_decode_roundtrip_preserves_shape(rgb_image: np.ndarray) -> None:
    jpeg = encode_jpeg(rgb_image)
    decoded = decode_jpeg(jpeg)

    assert isinstance(jpeg, bytes)
    assert len(jpeg) > 0
    assert decoded.shape == rgb_image.shape
    assert decoded.dtype == np.uint8


def test_encode_decode_is_lossy_but_close(rgb_image: np.ndarray) -> None:
    """JPEG is lossy; pixel values should be close, not identical."""
    decoded = decode_jpeg(encode_jpeg(rgb_image, quality=95))

    diff = np.abs(decoded.astype(int) - rgb_image.astype(int))
    # Tight bound on a flat-color image at high quality.
    assert diff.mean() < 5


def test_encode_rejects_non_rgb_array() -> None:
    grayscale = np.zeros((100, 100), dtype=np.uint8)

    with pytest.raises(ValueError, match="expected RGB image"):
        encode_jpeg(grayscale)


def test_decode_converts_grayscale_source_to_rgb(rgb_image: np.ndarray) -> None:
    """Even if the source is grayscale, decode_jpeg returns (H, W, 3)."""
    pil = Image.fromarray(rgb_image[:, :, 0], mode="L")
    buf = BytesIO()
    pil.save(buf, format="JPEG")

    decoded = decode_jpeg(buf.getvalue())

    assert decoded.shape == (100, 100, 3)
    assert decoded.dtype == np.uint8


# ---------- draw_bbox ----------


def test_draw_bbox_with_none_returns_unchanged_copy(rgb_image: np.ndarray) -> None:
    result = draw_bbox(rgb_image, None)

    assert result.shape == rgb_image.shape
    np.testing.assert_array_equal(result, rgb_image)
    # Returned array is a copy, not the same object.
    assert result is not rgb_image


def test_draw_bbox_paints_outline_in_specified_color(rgb_image: np.ndarray) -> None:
    bbox = BBox(x=20, y=20, w=40, h=40, confidence=0.9)

    result = draw_bbox(rgb_image, bbox, color=(255, 0, 0), thickness=2)

    # Top-left corner of the rectangle is exactly red.
    assert tuple(result[20, 20]) == (255, 0, 0)
    # Some pixels changed; the input was uniform green.
    diff_mask = (result != rgb_image).any(axis=2)
    assert diff_mask.sum() > 0


def test_draw_bbox_does_not_mutate_input(rgb_image: np.ndarray) -> None:
    original = rgb_image.copy()
    bbox = BBox(x=10, y=10, w=20, h=20, confidence=0.5)

    draw_bbox(rgb_image, bbox)

    np.testing.assert_array_equal(rgb_image, original)


def test_draw_bbox_rejects_non_rgb_array() -> None:
    grayscale = np.zeros((50, 50), dtype=np.uint8)
    bbox = BBox(x=0, y=0, w=10, h=10, confidence=0.5)

    with pytest.raises(ValueError, match="expected RGB image"):
        draw_bbox(grayscale, bbox)