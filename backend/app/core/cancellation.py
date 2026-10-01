"""Cooperative cancellation of a running scan.

A background scan runs on one worker thread. ``cancellation_scope`` binds a
token to that thread; long loops call ``raise_if_cancelled`` at safe points
and the scan stops there. Outside a scope (synchronous uploads, tests, worker
processes) the checks do nothing.

``ScanCancelled`` derives from ``BaseException`` so the many ``except
Exception`` fallbacks in the pipeline (sequential re-evaluation, retrieval
error wrapping, safe-failure handlers) cannot swallow a cancellation or turn
it into an ordinary failure.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager


class ScanCancelled(BaseException):
    """Raised at a checkpoint after the scan's cancellation was requested."""


class CancellationToken:
    def __init__(self):
        self._event = threading.Event()
        self.scan_id: int | None = None

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()


_state = threading.local()


@contextmanager
def cancellation_scope(token: CancellationToken):
    previous = getattr(_state, "token", None)
    _state.token = token
    try:
        yield token
    finally:
        _state.token = previous


def raise_if_cancelled() -> None:
    token = getattr(_state, "token", None)
    if token is not None and token.cancelled:
        raise ScanCancelled()


def bind_scan(scan_id: int) -> None:
    """Record which scan the current scope is producing, so it can be cancelled by id."""
    token = getattr(_state, "token", None)
    if token is not None:
        token.scan_id = scan_id
