"""In-process cache for immutable read models of completed scans.

Opening a large scan builds its identity read model from every stored record;
the results page, its group pages and the exports each asked for that same
build. A completed projection never changes, so it is built once per key and
reused. Concurrent requests for a key wait for the one build in progress
instead of starting their own.

Keys must identify persisted, immutable content (run id plus its stored
fingerprints), so a re-run or new projection never reads a stale entry.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Callable, Hashable, TypeVar

T = TypeVar("T")


class ReadModelCache:
    def __init__(self, max_entries: int):
        self._max_entries = max_entries
        self._entries: OrderedDict[Hashable, object] = OrderedDict()
        self._lock = threading.Lock()
        self._building: dict[Hashable, threading.Lock] = {}

    def get_or_build(self, key: Hashable, build: Callable[[], T]) -> T:
        with self._lock:
            if key in self._entries:
                self._entries.move_to_end(key)
                return self._entries[key]
            build_lock = self._building.setdefault(key, threading.Lock())
        with build_lock:
            with self._lock:
                if key in self._entries:
                    self._entries.move_to_end(key)
                    return self._entries[key]
            try:
                value = build()
            except BaseException:
                with self._lock:
                    self._building.pop(key, None)
                raise
            with self._lock:
                self._entries[key] = value
                while len(self._entries) > self._max_entries:
                    self._entries.popitem(last=False)
                self._building.pop(key, None)
            return value

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


# A 100k-record read model is large; keep only the most recently opened scans.
identity_snapshot_cache = ReadModelCache(max_entries=2)
targeted_explanation_cache = ReadModelCache(max_entries=4)
