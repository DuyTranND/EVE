import numpy as np

from src.utility.images import merge_image


def test_merge_image_clips_at_the_background_edge():
    background = np.zeros((4, 4, 3), dtype=np.uint8)
    foreground = np.full((3, 3, 3), 255, dtype=np.uint8)

    result = merge_image(background, foreground, 3, 3)

    assert np.array_equal(result[3, 3], [255, 255, 255])
    assert np.count_nonzero(result) == 3


def test_outside_image_does_not_change_background():
    background = np.zeros((4, 4, 3), dtype=np.uint8)
    foreground = np.full((2, 2, 3), 255, dtype=np.uint8)
    assert np.array_equal(merge_image(background, foreground, 10, 10), background)
