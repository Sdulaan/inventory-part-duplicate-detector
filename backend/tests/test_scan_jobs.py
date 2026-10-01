import threading
import time

from fastapi import HTTPException

from app.services.scan_jobs import (
    COMPLETED,
    FAILED,
    ScanJobRegistry,
    ThreadedBackgroundTasks,
)

CSV = (
    b"PART_NO,DESCRIPTION,CONTRACT,UNIT_MEAS\n"
    b"294636,Filtmatta 20x30cm 100st/bunt,S1,ST\n"
    b"294637,Filtmatta 30x20cm 100st/bunt,S1,ST\n"
    b"322585,Salvia hybrid Rockin' Lavender,S1,ST\n"
    b"330390,Salvia hybrid Rockin' Lavender,S1,ST\n"
)
FORM = {"selected_fields": '["CONTRACT","UNIT_MEAS"]', "threshold": "75"}


def _wait(client, job_id, timeout=60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = client.get(f"/api/scans/jobs/{job_id}").json()
        if job["status"] in {COMPLETED, FAILED}:
            return job
        time.sleep(0.05)
    raise AssertionError("scan job did not finish")


def _wait_registry(registry, job_id, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = registry.get(job_id)
        if job["status"] in {COMPLETED, FAILED}:
            return job
        time.sleep(0.01)
    raise AssertionError("scan job did not finish")


def test_async_upload_returns_a_job_then_the_same_result_as_upload(client):
    started = client.post(
        "/api/scans/upload-async",
        files={"file": ("async.csv", CSV, "text/csv")}, data=FORM,
    )
    assert started.status_code == 202
    assert started.json()["job_id"]

    job = _wait(client, started.json()["job_id"])
    assert job["status"] == COMPLETED, job
    assert job["error"] is None
    assert job["stage"]
    result = job["result"]
    assert result["scan_id"] > 0

    synchronous = client.post(
        "/api/scans/upload", files={"file": ("sync.csv", CSV, "text/csv")}, data=FORM,
    ).json()
    assert set(result) == set(synchronous)
    assert result["total_records"] == synchronous["total_records"] == 4
    groups = client.get(f"/api/scans/{result['scan_id']}/identity-read/summary")
    assert groups.status_code == 200


def test_async_upload_rejects_invalid_files_before_queueing(client):
    response = client.post(
        "/api/scans/upload-async",
        files={"file": ("bad.csv", b"PART_NO,CONTRACT\nA,S1\n", "text/csv")},
        data=FORM,
    )
    assert response.status_code == 422
    assert "job_id" not in response.json()


def test_unknown_scan_job_is_not_found(client):
    assert client.get("/api/scans/jobs/does-not-exist").status_code == 404


def test_registry_reports_stages_and_failures():
    registry = ScanJobRegistry()
    release = threading.Event()

    def slow(report_stage):
        report_stage("DISCOVERY")
        release.wait(5)
        return {"scan_id": 7}

    job = registry.submit(slow)
    deadline = time.monotonic() + 5
    while registry.get(job["job_id"])["stage"] != "DISCOVERY":
        assert time.monotonic() < deadline
        time.sleep(0.01)
    assert registry.get(job["job_id"])["status"] == "RUNNING"
    release.set()
    assert _wait_registry(registry, job["job_id"])["result"] == {"scan_id": 7}

    def rejected(_report_stage):
        raise HTTPException(422, {"category": "validation_failure"})

    failed = _wait_registry(registry, registry.submit(rejected)["job_id"])
    assert failed["status"] == FAILED
    assert failed["error"]["status_code"] == 422

    def crashed(_report_stage):
        raise RuntimeError("secret internal detail")

    crashed_job = _wait_registry(registry, registry.submit(crashed)["job_id"])
    assert crashed_job["error"]["status_code"] == 500
    assert "secret" not in str(crashed_job["error"])


def test_registry_runs_one_scan_at_a_time_and_prunes_finished_jobs():
    registry = ScanJobRegistry(retained_finished_jobs=2)
    running = []
    overlap = []

    def work(_report_stage):
        running.append(1)
        overlap.append(len(running))
        time.sleep(0.02)
        running.pop()
        return {}

    ids = [registry.submit(work)["job_id"] for _ in range(4)]
    _wait_registry(registry, ids[-1])
    assert max(overlap) == 1
    registry.submit(work)
    assert registry.get(ids[0]) is None


def test_threaded_background_tasks_run_off_the_scan_thread():
    done = threading.Event()
    seen = []
    ThreadedBackgroundTasks().add_task(
        lambda value: (seen.append((value, threading.current_thread().name)), done.set()),
        "triage",
    )
    assert done.wait(5)
    assert seen == [("triage", "scan-follow-up")]


def test_scans_left_running_by_a_restart_are_marked_failed(db):
    from app.db.models import DuplicateScan, ScanOrchestrationRun
    from app.services.scan_jobs import fail_interrupted_scans

    interrupted = DuplicateScan(
        scan_name="interrupted", threshold=75, status="RUNNING",
        model_version="test", selected_fields="[]",
    )
    finished = DuplicateScan(
        scan_name="finished", threshold=75, status="COMPLETED",
        model_version="test", selected_fields="[]",
    )
    db.add_all([interrupted, finished])
    db.flush()
    db.add(ScanOrchestrationRun(
        scan_id=interrupted.id, mode="group_first_primary", policy_version="v",
        policy_fingerprint="p" * 64, plan_fingerprint="q" * 64,
        primary_identity_pipeline="GROUP_FIRST_GF1_GF6",
        visible_projection_contract="G2_V2",
        compatibility_projection_required=False, status="RUNNING",
    ))
    db.commit()

    class _SharedSession:
        """Hands the test session to the function without closing it."""

        def __call__(self):
            return self

        def __getattr__(self, name):
            return getattr(db, name)

        def close(self):
            pass

    assert fail_interrupted_scans(_SharedSession()) == [interrupted.id]
    db.expire_all()
    assert db.get(DuplicateScan, interrupted.id).status == "FAILED"
    assert db.get(DuplicateScan, interrupted.id).completed_at is not None
    assert db.get(DuplicateScan, finished.id).status == "COMPLETED"
    run = db.query(ScanOrchestrationRun).filter_by(scan_id=interrupted.id).one()
    assert run.status == "FAILED" and run.visible_product_ready is False
    assert fail_interrupted_scans(_SharedSession()) == []


def test_queued_job_cancelled_before_it_starts_never_runs():
    registry = ScanJobRegistry()
    release = threading.Event()
    ran = []
    blocker = registry.submit(lambda report: release.wait(5) and {})
    queued = registry.submit(lambda report: ran.append(True) or {})
    assert registry.cancel(queued["job_id"])["status"] == "CANCELLED"
    release.set()
    deadline = time.monotonic() + 5
    while registry.get(blocker["job_id"])["status"] != COMPLETED:
        assert time.monotonic() < deadline
        time.sleep(0.01)
    time.sleep(0.05)
    assert ran == []
    assert registry.get(queued["job_id"])["status"] == "CANCELLED"


def test_running_job_stops_at_its_next_checkpoint():
    from app.core.cancellation import bind_scan, raise_if_cancelled

    registry = ScanJobRegistry()
    started = threading.Event()
    reached_end = []

    def work(report):
        bind_scan(42)
        started.set()
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            raise_if_cancelled()
            time.sleep(0.01)
        reached_end.append(True)
        return {}

    job = registry.submit(work)
    assert started.wait(5)
    assert registry.get(job["job_id"])["scan_id"] == 42
    assert registry.cancel_scan(42)["cancel_requested"] is True
    deadline = time.monotonic() + 5
    while registry.get(job["job_id"])["status"] == "RUNNING":
        assert time.monotonic() < deadline
        time.sleep(0.01)
    assert registry.get(job["job_id"])["status"] == "CANCELLED"
    assert reached_end == []
    assert registry.cancel_scan(42) is None


def test_cancelled_scan_runner_marks_the_scan_cancelled(db):
    import pandas as pd

    from app.core.cancellation import CancellationToken, ScanCancelled, cancellation_scope
    from app.db.models import DuplicateScan, ScanOrchestrationRun
    from app.services.scan_runner import ScanRunner
    from test_group_first_scan_orchestration import configuration

    records = pd.DataFrame([
        {"PART_NO": "A", "DESCRIPTION": "SKF BEARING 6205", "CONTRACT": "S1", "UNIT_MEAS": "PCS"},
        {"PART_NO": "B", "DESCRIPTION": "SKF BEARING 6205", "CONTRACT": "S1", "UNIT_MEAS": "PCS"},
    ])
    token = CancellationToken()
    token.cancel()
    with cancellation_scope(token):
        try:
            ScanRunner(db, configuration("group_first_primary")).run(
                records, "cancelled", ["CONTRACT", "UNIT_MEAS"], 75
            )
        except ScanCancelled:
            pass
        else:
            raise AssertionError("cancelled scan ran to completion")
    scan = db.query(DuplicateScan).filter_by(id=token.scan_id).one()
    assert scan.status == "CANCELLED" and scan.completed_at is not None
    run = db.query(ScanOrchestrationRun).filter_by(scan_id=scan.id).one()
    assert run.status == "FAILED"


def test_cancel_endpoint_stops_a_scan_left_running_by_an_earlier_process(client, db):
    from app.db.models import DuplicateScan

    orphan = DuplicateScan(
        scan_name="orphan", threshold=75, status="RUNNING",
        model_version="test", selected_fields="[]",
    )
    db.add(orphan)
    db.commit()
    response = client.post(f"/api/scans/{orphan.id}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"
    db.expire_all()
    assert db.get(DuplicateScan, orphan.id).status == "CANCELLED"
    again = client.post(f"/api/scans/{orphan.id}/cancel")
    assert again.status_code == 409
    assert client.post("/api/scans/999999/cancel").status_code == 404
    assert client.post("/api/scans/jobs/unknown/cancel").status_code == 404
