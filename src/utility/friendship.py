"""Persistence helpers for EVE's friendliness score."""

from __future__ import annotations

from pathlib import Path


def load_friendliness(path: str | Path, default: float = 70.0) -> float:
    try:
        value = float(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default
    return max(0.0, min(100.0, value))


def save_friendliness(path: str | Path, value: float) -> None:
    value = max(0.0, min(100.0, value))
    Path(path).write_text(f"{value}", encoding="utf-8")
