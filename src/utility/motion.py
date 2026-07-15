"""Pure differential-drive motion calculations."""

from __future__ import annotations


def differential_wheel_speeds(
    linear_percent: float,
    angular_percent: float,
    *,
    wheel_radius: float,
    axle_length: float,
    max_wheel_speed: float,
) -> tuple[float, float]:
    """Convert normalized linear/angular commands to left/right wheel speeds."""
    linear_percent = max(-100.0, min(100.0, linear_percent))
    angular_percent = max(-100.0, min(100.0, angular_percent))
    max_linear = wheel_radius * max_wheel_speed
    max_angular = 2 * wheel_radius * max_wheel_speed / axle_length
    velocity = max_linear * linear_percent / 100.0
    omega = max_angular * angular_percent / 100.0
    half_turn_velocity = omega * axle_length / 2.0
    velocity = max(min(velocity, max_linear - half_turn_velocity), -max_linear - half_turn_velocity)
    right = (2 * velocity + omega * axle_length) / (2 * wheel_radius)
    left = (2 * velocity - omega * axle_length) / (2 * wheel_radius)
    return (
        max(-max_wheel_speed, min(max_wheel_speed, left)),
        max(-max_wheel_speed, min(max_wheel_speed, right)),
    )
