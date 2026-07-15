"""Validated MQTT payload codecs used by EVE services."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


def _comma_separated_floats(payload: bytes, expected: int) -> list[float]:
    text = payload.decode("utf-8")
    parts = text.split(",")
    if len(parts) != expected:
        raise ValueError(f"Expected {expected} comma-separated values, received {len(parts)}")
    return [float(part) for part in parts]


@dataclass(frozen=True)
class DepthReading:
    left: float
    front: float
    right: float

    @classmethod
    def from_payload(cls, payload: bytes, scale: float = 255.0) -> "DepthReading":
        values = _comma_separated_floats(payload, 3)
        return cls(*(round(value / scale, 2) for value in values))

    def as_list(self) -> list[float]:
        return [self.left, self.front, self.right]


@dataclass(frozen=True)
class TrackReading:
    horizontal_error: float
    width: float

    @classmethod
    def from_payload(cls, payload: bytes) -> "TrackReading":
        return cls(*_comma_separated_floats(payload, 2))

    def as_list(self) -> list[float]:
        return [self.horizontal_error, self.width]


def decode_detection(payload: bytes) -> dict[str, Any]:
    value = json.loads(payload.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Detection payload must be a JSON object")
    return value
