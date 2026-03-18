from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any


class TTLCache:
    def __init__(self, ttl_seconds: int = 300, max_entries: int = 256) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._data: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            self._evict_expired()
            record = self._data.get(key)
            if record is None:
                return None
            expires_at, value = record
            if expires_at < time.time():
                self._data.pop(key, None)
                return None
            self._data.move_to_end(key)
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._evict_expired()
            self._data[key] = (time.time() + self.ttl_seconds, value)
            self._data.move_to_end(key)
            while len(self._data) > self.max_entries:
                self._data.popitem(last=False)

    def _evict_expired(self) -> None:
        now = time.time()
        expired_keys = [key for key, (expires_at, _) in self._data.items() if expires_at < now]
        for key in expired_keys:
            self._data.pop(key, None)

