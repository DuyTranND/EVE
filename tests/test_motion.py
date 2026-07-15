import pytest

from src.utility.motion import differential_wheel_speeds


PARAMS = {
    "wheel_radius": 0.085,
    "axle_length": 0.17,
    "max_wheel_speed": 13.0,
}


def test_full_speed_straight_ahead():
    left, right = differential_wheel_speeds(100, 0, **PARAMS)
    assert left == pytest.approx(13.0)
    assert right == pytest.approx(13.0)


def test_turn_in_place():
    left, right = differential_wheel_speeds(0, 100, **PARAMS)
    assert left == pytest.approx(-13.0)
    assert right == pytest.approx(13.0)


def test_commands_are_clamped():
    left, right = differential_wheel_speeds(500, 0, **PARAMS)
    assert left == pytest.approx(13.0)
    assert right == pytest.approx(13.0)
