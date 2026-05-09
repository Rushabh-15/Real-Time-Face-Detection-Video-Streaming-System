"""Shared pytest fixtures for the backend test suite."""

import numpy as np
import pytest


@pytest.fixture
def rgb_image() -> np.ndarray:
    """A 100x100 RGB image with a solid mid-green tint.

    Suitable for codec round-trip and drawing tests where the content
    doesn't matter — only shape, dtype, and structural integrity.
    """
    arr = np.zeros((100, 100, 3), dtype=np.uint8)
    arr[:, :, 1] = 128
    return arr