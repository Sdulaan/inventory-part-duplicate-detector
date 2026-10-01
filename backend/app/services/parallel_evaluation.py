"""Pair evaluation spread across worker processes for large scans.

Scoring a candidate pair is pure and independent of every other pair, but
Python runs it on one core. Large scans score tens of thousands of pairs, so
they are split into ordered chunks for a process pool; results are returned
in the original order, so persisted evidence is identical to a sequential run.

Workers are started with "spawn": the backend is multi-threaded (web server,
scan job thread), and forking a threaded process can deadlock.
"""

from __future__ import annotations

import logging
import math
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

from app.core.cancellation import raise_if_cancelled
from app.core.config import settings
from app.engine.identity_evidence_evaluator import (
    evaluate_canonical_identity_relationship,
)

logger = logging.getLogger(__name__)

# Below this many pairs, starting workers costs more than it saves.
PARALLEL_MIN_PAIRS = 5_000
_CHUNKS_PER_WORKER = 8
# Pairs evaluated between cancellation checks on the sequential path.
_CANCEL_CHECK_INTERVAL = 500

_worker_records = None
_worker_context = None


def _initialise_worker(records_by_id, context) -> None:
    global _worker_records, _worker_context
    _worker_records = records_by_id
    _worker_context = context


def _evaluate_chunk(pairs):
    return [
        evaluate_canonical_identity_relationship(
            _worker_records[left], _worker_records[right], _worker_context
        )
        for left, right in pairs
    ]


def configured_worker_count() -> int:
    return max(1, int(getattr(settings, "scan_worker_processes", 1) or 1))


def evaluate_canonical_pairs(records_by_id, context, pairs, *, workers=None):
    """Evaluate ``(record_id_1, record_id_2)`` pairs, preserving their order."""
    workers = configured_worker_count() if workers is None else workers
    if workers > 1 and len(pairs) >= PARALLEL_MIN_PAIRS:
        try:
            return _evaluate_in_pool(records_by_id, context, pairs, workers)
        except Exception:
            # A worker can die (e.g. under memory pressure) and break the pool.
            # Evaluation is deterministic, so a sequential rerun gives the same
            # result; any genuine evaluation error is raised again below.
            logger.warning(
                "parallel pair evaluation failed; evaluating sequentially", exc_info=True
            )
    results = []
    for index, (left, right) in enumerate(pairs):
        if index % _CANCEL_CHECK_INTERVAL == 0:
            raise_if_cancelled()
        results.append(evaluate_canonical_identity_relationship(
            records_by_id[left], records_by_id[right], context
        ))
    return results


def _evaluate_in_pool(records_by_id, context, pairs, workers):
    needed = {record_id for pair in pairs for record_id in pair}
    records = {record_id: records_by_id[record_id] for record_id in needed}
    size = max(1, math.ceil(len(pairs) / (workers * _CHUNKS_PER_WORKER)))
    chunks = [pairs[start:start + size] for start in range(0, len(pairs), size)]
    pool = ProcessPoolExecutor(
        max_workers=workers,
        mp_context=multiprocessing.get_context("spawn"),
        initializer=_initialise_worker,
        initargs=(records, context),
    )
    try:
        results = []
        for chunk in pool.map(_evaluate_chunk, chunks):
            raise_if_cancelled()
            results.extend(chunk)
        return results
    finally:
        # On cancellation, drop chunks not yet started instead of waiting.
        pool.shutdown(wait=True, cancel_futures=True)
