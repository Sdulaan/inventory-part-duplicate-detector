"""Background execution for uploaded scans.

A large scan can run for many minutes. Running it inside the upload request
kept the connection open past proxy timeouts and blocked every other request,
so uploads are queued here and the browser polls the job for progress.

Jobs run one at a time so two large scans never compete for memory or the
SQLite writer. Job status is kept in memory: after a backend restart an
unfinished job is unknown and its partial scan remains in the scan history.
"""

from __future__ import annotations

import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Callable

from fastapi import HTTPException

logger = logging.getLogger(__name__)

QUEUED = "QUEUED"
RUNNING = "RUNNING"
COMPLETED = "COMPLETED"
FAILED = "FAILED"

_FINISHED = {COMPLETED, FAILED}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ScanJobRegistry:
    def __init__(self, *, max_workers: int = 1, retained_finished_jobs: int = 50):
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="scan-job"
        )
        self._lock = threading.Lock()
        self._jobs: dict[str, dict] = {}
        self._retained = retained_finished_jobs

    def submit(self, work: Callable[[Callable[[str], None]], dict]) -> dict:
        """Queue ``work(report_stage)``; it returns the completed scan payload."""
        job_id = uuid.uuid4().hex
        job = {
            "job_id": job_id,
            "status": QUEUED,
            "stage": None,
            "submitted_at": _now(),
            "started_at": None,
            "finished_at": None,
            "result": None,
            "error": None,
        }
        with self._lock:
            self._jobs[job_id] = job
            self._prune()
        self._executor.submit(self._execute, job_id, work)
        return self.get(job_id)

    def get(self, job_id: str) -> dict | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return None if job is None else dict(job)

    def _update(self, job_id: str, **changes) -> None:
        with self._lock:
            self._jobs[job_id].update(changes)

    def _execute(self, job_id: str, work) -> None:
        self._update(job_id, status=RUNNING, started_at=_now())
        try:
            result = work(lambda stage: self._update(job_id, stage=stage))
        except HTTPException as exc:
            self._update(
                job_id, status=FAILED, finished_at=_now(),
                error={"status_code": exc.status_code, "detail": exc.detail},
            )
        except Exception:
            logger.exception("background scan job %s failed", job_id)
            self._update(
                job_id, status=FAILED, finished_at=_now(),
                error={
                    "status_code": 500,
                    "detail": {"category": "scan_failure", "message": "Scan failed safely"},
                },
            )
        else:
            self._update(job_id, status=COMPLETED, finished_at=_now(), result=result)

    def _prune(self) -> None:
        finished = [
            job_id for job_id, job in self._jobs.items() if job["status"] in _FINISHED
        ]
        for job_id in finished[: max(0, len(finished) - self._retained)]:
            del self._jobs[job_id]


class ThreadedBackgroundTasks:
    """Stand-in for a request's BackgroundTasks outside a request.

    Follow-up work such as automatic LLM triage runs on its own thread so the
    next queued scan does not wait for it.
    """

    def add_task(self, func, *args, **kwargs) -> None:
        threading.Thread(
            target=func, args=args, kwargs=kwargs, daemon=True,
            name="scan-follow-up",
        ).start()


scan_jobs = ScanJobRegistry()


def get_scan_jobs() -> ScanJobRegistry:
    return scan_jobs
