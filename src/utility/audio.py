"""Audio playback without import-time mixer initialization."""

from __future__ import annotations

import os
from pathlib import Path
from threading import RLock

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
_mixer_lock = RLock()
_mixer_ready = False


def _ensure_mixer():
    global _mixer_ready
    if not _mixer_ready:
        with _mixer_lock:
            if not _mixer_ready:
                import pygame

                pygame.mixer.init()
                _mixer_ready = True
    import pygame
    return pygame


def play_sound(path: str | Path, wait: bool = False) -> bool:
    """Play a sound asset and return whether the file existed."""
    path = Path(path)
    if not path.exists():
        return False
    pygame = _ensure_mixer()
    sound = pygame.mixer.Sound(str(path))
    sound.set_volume(1.0)
    sound.play()
    if wait:
        pygame.time.wait(int(sound.get_length() * 1000))
    return True
