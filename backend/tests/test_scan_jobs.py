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
