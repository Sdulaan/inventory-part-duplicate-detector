import threading

import pytest

from app.services.read_cache import ReadModelCache


def test_concurrent_requests_share_one_build():
    cache = ReadModelCache(max_entries=2)
    started = threading.Event()
    release = threading.Event()
    builds = []

    def build():
        builds.append(1)
        started.set()
        release.wait(5)
        return "snapshot"

    results = []
    threads = [
        threading.Thread(target=lambda: results.append(cache.get_or_build("scan-15", build)))
        for _ in range(4)
    ]
    for thread in threads:
        thread.start()
    assert started.wait(5)
    release.set()
    for thread in threads:
        thread.join(5)

    assert results == ["snapshot"] * 4
    assert len(builds) == 1


def test_only_the_most_recent_entries_are_kept():
    cache = ReadModelCache(max_entries=2)
    builds = []
    for key in ("a", "b", "a", "c"):
        cache.get_or_build(key, lambda key=key: builds.append(key) or key)
    cache.get_or_build("a", lambda: builds.append("a again") or "a")
    cache.get_or_build("b", lambda: builds.append("b again") or "b")
    assert builds == ["a", "b", "c", "b again"]


def test_failed_build_is_not_cached():
    cache = ReadModelCache(max_entries=2)

    def failing():
        raise ValueError("not ready")

    with pytest.raises(ValueError):
        cache.get_or_build("scan", failing)
    assert cache.get_or_build("scan", lambda: "built") == "built"
