"""Pure image composition helpers."""

from __future__ import annotations

import numpy as np


def merge_image(back: np.ndarray, front: np.ndarray, x: int, y: int) -> np.ndarray:
    """Place ``front`` over ``back`` while clipping it to the background."""
    background_height, background_width = back.shape[:2]
    foreground_height, foreground_width = front.shape[:2]
    x1, x2 = max(x, 0), min(x + foreground_width, background_width)
    y1, y2 = max(y, 0), min(y + foreground_height, background_height)
    result = back.copy()
    if x1 >= x2 or y1 >= y2:
        return result
    result[y1:y2, x1:x2] = front[y1 - y:y2 - y, x1 - x:x2 - x]
    return result
