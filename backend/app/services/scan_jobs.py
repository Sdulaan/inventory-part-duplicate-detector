"""Background execution for uploaded scans.

A large scan can run for many minutes. Running it inside the upload request
kept the connection open past proxy timeouts and blocked every other request,
so uploads are queued here and the browser polls the job for progress.

Jobs run one at a time so two large scans never compete for memory or the
SQLite writer. Job status is kept in memory, so a backend restart loses every
unfinished job; ``fail_interrupted_scans`` runs at startup and marks the scans
those jobs left RUNNING as FAILED instead of leaving them processing forever.
This assumes one backend process owns the database, as deployed.
"""

from __future__ import annotations

import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Callable

from fastapi import HTTPException

from app.core.cancellation import CancellationToken, ScanCancelled, cancellation_scope

logger = logging.getLogger(__name__)

QUEUED = "QUEUED"
RUNNING = "RUNNING"
COMPLETED = "COMPLETED"
FAILED = "FAILED"
CANCELLED = "CANCELLED"

_FINISHED = {COMPLETED, FAILED, CANCELLED}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ScanJobRegistry:
    def __init__(self, *, max_workers: int = 1, retained_finished_jobs: int = 50):
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="scan-job"
        )
        self._lock = threading.Lock()
        self._jobs: dict[str, dict] = {}
        self._tokens: dict[str, CancellationToken] = {}
        self._retained = retained_finished_jobs

    def submit(self, work: Callable[[Callable[[str], None]], dict]) -> dict:
        """Queue ``work(report_stage)``; it returns the completed scan payload."""
        job_id = uuid.uuid4().hex
        job = {
            "job_id": job_id,
            "status": QUEUED,
            "stage": None,
            "scan_id": None,
            "cancel_requested": False,
            "submitted_at": _now(),
            "started_at": None,
            "finished_at": None,
            "result": None,
            "error": None,
        }
        with self._lock:
            self._jobs[job_id] = job
            self._tokens[job_id] = CancellationToken()
            self._prune()
        self._executor.submit(self._execute, job_id, work)
        return self.get(job_id)

    def get(self, job_id: str) -> dict | None:
        with self._lock:
            return self._snapshot(job_id)

    def cancel(self, job_id: str) -> dict | None:
        """Request cancellation; a queued job never starts, a running one stops
        at its next checkpoint. Finished jobs are returned unchanged."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            if job["status"] not in _FINISHED:
                self._tokens[job_id].cancel()
                job["cancel_requested"] = True
                if job["status"] == QUEUED:
                    job.update(status=CANCELLED, finished_at=_now())
            return self._snapshot(job_id)

    def cancel_scan(self, scan_id: int) -> dict | None:
        """Cancel the unfinished job producing ``scan_id``, if this process runs one."""
        with self._lock:
            job_id = next((
                job_id for job_id, token in self._tokens.items()
                if token.scan_id == scan_id
                and self._jobs[job_id]["status"] not in _FINISHED
            ), None)
        return None if job_id is None else self.cancel(job_id)

    def _snapshot(self, job_id: str) -> dict | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        snapshot = dict(job)
        snapshot["scan_id"] = self._tokens[job_id].scan_id
        return snapshot

    def _update(self, job_id: str, **changes) -> None:
        with self._lock:
            self._jobs[job_id].update(changes)

    def _execute(self, job_id: str, work) -> None:
        with self._lock:
            # A job cancelled while queued never starts.
            if self._jobs[job_id]["status"] != QUEUED:
                return
            self._jobs[job_id].update(status=RUNNING, started_at=_now())
            token = self._tokens[job_id]
        try:
            with cancellation_scope(token):
                result = work(lambda stage: self._update(job_id, stage=stage))
        except ScanCancelled:
            logger.info("background scan job %s was cancelled", job_id)
            self._update(job_id, status=CANCELLED, finished_at=_now())
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
            del self._tokens[job_id]


def stop_running_scans(db, status: str, scan_ids=None) -> list[int]:
    """Set RUNNING scans (all, or ``scan_ids``) and their RUNNING pipeline runs
    to ``status`` (FAILED or CANCELLED) and commit. Returns the scan ids."""
    from app.db.models import (
        DuplicateScan, G2V2ProjectionRun, IdentityDiscoveryRun,
        IdentityEvidenceRun, IdentityResolutionRun, ScanOrchestrationRun,
        ShadowComparisonRun,
    )
    from app.orchestration.contracts import OrchestrationFailureCategory

    def running(model):
        query = db.query(model).filter_by(status=RUNNING)
        if scan_ids is not None:
            query = query.filter(model.scan_id.in_(scan_ids))
        return query.all()

    now = datetime.now(timezone.utc)
    query = db.query(DuplicateScan).filter_by(status=RUNNING)
    if scan_ids is not None:
        query = query.filter(DuplicateScan.id.in_(scan_ids))
    scans = query.all()
    stopped = [scan.id for scan in scans]
    for scan in scans:
        scan.status = status
        scan.completed_at = now
    # Pipeline-run tables only allow RUNNING/COMPLETED/FAILED.
    for run in running(ScanOrchestrationRun):
        run.status = FAILED
        run.completed_at = now
        run.primary_identity_ready = False
        run.compatibility_projection_ready = False
        run.visible_product_ready = False
        run.shadow_diagnostics_ready = False
        run.safe_failure_category = (
            OrchestrationFailureCategory.PRIMARY_IDENTITY_FAILED.value
        )
    for model in (
        IdentityDiscoveryRun, IdentityEvidenceRun, IdentityResolutionRun,
        G2V2ProjectionRun, ShadowComparisonRun,
    ):
        for run in running(model):
            run.status = FAILED
            run.completed_at = now
            if hasattr(run, "safe_failure_category"):
                run.safe_failure_category = (
                    "CANCELLED" if status == CANCELLED else "INTERRUPTED_BY_RESTART"
                )
    db.commit()
    return stopped


def fail_interrupted_scans(session_factory) -> list[int]:
    """Mark scans and pipeline runs left RUNNING by a previous process FAILED.

    Called once at startup, before any job can run, so nothing RUNNING can
    belong to this process.
    """
    db = session_factory()
    try:
        scan_ids = stop_running_scans(db, FAILED)
    except Exception:
        db.rollback()
        logger.exception("could not mark interrupted scans as failed")
        return []
    finally:
        db.close()
    if scan_ids:
        logger.warning("marked scans interrupted by a restart as FAILED: %s", scan_ids)
    return scan_ids


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
