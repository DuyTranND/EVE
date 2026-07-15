"""Thread-safe lazy initialization for hardware and network resources."""

from __future__ import annotations

from importlib import import_module
from threading import RLock
from typing import Any


class LazyResource:
    """Instantiate a resource only when one of its attributes is first used."""

    def __init__(self, module: str, class_name: str, *args: Any, **kwargs: Any) -> None:
        self._module = module
        self._class_name = class_name
        self._args = args
        self._kwargs = kwargs
        self._instance: Any | None = None
        self._lock = RLock()

    def get(self) -> Any:
        if self._instance is None:
            with self._lock:
                if self._instance is None:
                    cls = getattr(import_module(self._module), self._class_name)
                    self._instance = cls(*self._args, **self._kwargs)
        return self._instance

    @property
    def initialized(self) -> bool:
        return self._instance is not None

    def close(self, method: str) -> None:
        if self._instance is not None:
            getattr(self._instance, method)()

    def __getattr__(self, name: str) -> Any:
        return getattr(self.get(), name)
