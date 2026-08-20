from __future__ import annotations

import time
from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    """Small in-process cache; replace with Redis when running multiple replicas."""

    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self._values: dict[str, tuple[float, T]] = {}

    def get_or_set(self, key: str, factory: Callable[[], T]) -> T:
        now = time.monotonic()
        cached = self._values.get(key)
        if cached and now - cached[0] < self.ttl_seconds:
            return cached[1]
        value = factory()
        self._values[key] = (now, value)
        return value

