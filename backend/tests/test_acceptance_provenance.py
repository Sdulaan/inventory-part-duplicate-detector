"""Acceptance-artifact provenance contracts; never exercises providers."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.benchmarks.acceptance_provenance import (
    CANONICAL_SERIALIZATION,
    SCHEMA_VERSION,
    UnsafeProvenanceError,
    build_scan_manifest,
    canonical_json,
    input_provenance,
    repository_provenance,
    request_provenance,
    stable_sha256,
    write_manifest,
)


HISTORICAL_HASHES = (
    "8107a36194f3bab4209a1f714fc7412a76288b11b2a7b93d536a9c20b55d6257",
    "4f2df0eb716ec0d9b06ec65c33cfb6cca1673ccce84559dfe56fbc9f42cdd2fd",
    "726f1206ede9210c10fdcc797c594523887a41156453cb981c82315a0d9ad38f",
    "682473a17a9edcbf66e940194a6287852a057f32655863948459bb12fc975468",
    "7fe6c3e5138cf3274ccc8bcf786f6accd1528af3e9690f06d20230a6b5c97259",
    "268e78c48b662ff301dde75d68a4792e994350b41f2dc4c9abc2aff0cbbdb6b9",
    "a84dbe3aca0391c688ab79ea0723bc95b168d70ef0741a1c09259f43fe7c006a",
    "aeecfb4f30e9a00819fc2a6b5f414e55768032730d2a67805f646d3f7c0af860",
    "6de165cafcdd79dfb469e5060b604ab19d84fb0b31e590edcbeb40c71b9ae2b0",
    "cdbab036c0dad18e918c56edb0a976d24317a74d3240cfe82a0ea99e7e2742c6",
    "0a8a5ba1c699d9f810d1c555509a462d04530b113f8564c8c9d9b5edd92e341b",
)
STAGE_COUNTS = (2, 20492, 20492, 20492, 1313, 1, 158, 27, 40, 4982, 158)


class FakeAudit:
    scan_id = 1
    records = (
        {"source_row_index": 0, "source_record_fingerprint": "a" * 64},
        {"source_row_index": 1, "source_record_fingerprint": "b" * 64},
    )

    def stages(self):
        return tuple(
            SimpleNamespace(
                stage=f"S{index}_STAGE_{index}",
                count=STAGE_COUNTS[index],
                fingerprint=HISTORICAL_HASHES[index],
            )
            for index in range(11)
        )


def database(*, provider_calls: int = 0) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        create table duplicate_scan (
          id integer, selected_fields text, threshold real, scan_mode text,
          source_type text
        );
        create table identity_discovery_run (
          id integer, scan_id integer, algorithm_version text,
          configuration_version text, normalization_version text,
          configuration_json text, proposal_count integer,
          provider_request_count integer
        );
        create table identity_evidence_run (
          id integer, scan_id integer, algorithm_version text,
          configuration_fingerprint text
        );
        create table identity_resolution_run (
          id integer, scan_id integer, resolver_algorithm_version text,
          configuration_version text, configuration_fingerprint text,
          configuration_json text, source_record_count integer,
          accepted_group_count integer, likely_group_count integer,
          review_group_count integer, conflict_count integer,
          deferred_work_unit_count integer, unassigned_record_count integer,
          targeted_evidence_request_count integer,
          candidate_partitions_explored integer, provider_request_count integer
        );
        create table g2_v2_projection_run (
          id integer, scan_id integer, adapter_algorithm_version text,
          adapter_configuration_fingerprint text, snapshot_contract_version integer
        );
        create table scan_orchestration_run (
          id integer, scan_id integer, mode text, policy_version text,
          policy_fingerprint text, primary_identity_pipeline text,
          visible_projection_contract text
        );
        create table hybrid_retrieval_run (
          id integer, scan_id integer, provider_request_count integer
        );
        create table g2_v2_group_member (id integer, projection_run_id integer);
        """
    )
    discovery_configuration = {
        "configuration_version": "identity-discovery-config-v6",
        "scan_mode": "DISCOVERY",
        "selected_fields": ["CONTRACT", "UNIT_MEAS"],
        "hybrid_enabled": True,
        "local_embedding_enabled": True,
        "local_embedding_model": "sklearn-hashing-domain-v1",
        "hybrid_global_cap": 500,
    }
    connection.execute(
        "insert into duplicate_scan values (1,?,?,?,?)",
        (json.dumps(["CONTRACT", "UNIT_MEAS"]), 75, "SAME_SITE_DUPLICATE", "CSV"),
    )
    connection.execute(
        "insert into identity_discovery_run values (1,1,?,?,?,?,?,?)",
        (
            "identity-discovery-v6-scan-independent-ordering",
            "identity-discovery-config-v6",
            "hybrid-nlp-v1",
            json.dumps(discovery_configuration),
            20492,
            provider_calls,
        ),
    )
    connection.execute(
        "insert into identity_evidence_run values (1,1,?,?)",
        ("independent-identity-evidence-v1", "c" * 64),
    )
    connection.execute(
        "insert into identity_resolution_run values (1,1,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "constrained-identity-resolver-v2-stable-ordering",
            "constrained-identity-resolver-config-v1",
            "d" * 64,
            json.dumps({
                "configuration_version": "constrained-identity-resolver-config-v1",
                "max_resolution_members": 20,
                "max_targeted_checks_per_work_unit": 40,
            }),
            2,
            158,
            45,
            113,
            27,
            40,
            4982,
            271,
            171251,
            provider_calls,
        ),
    )
    connection.execute(
        "insert into g2_v2_projection_run values (1,1,?,?,?)",
        ("g2-v2-resolution-adapter-v1", "e" * 64, 2),
    )
    connection.execute(
        "insert into scan_orchestration_run values (1,1,?,?,?,?,?)",
        (
            "group_first_primary",
            "group-first-orchestration-policy-v2",
            "f" * 64,
            "GROUP_FIRST_GF1_GF6",
            "G2_V2",
        ),
    )
    connection.execute(
        "insert into hybrid_retrieval_run values (1,1,?)", (provider_calls,)
    )
    connection.executemany(
        "insert into g2_v2_group_member values (?,1)", ((index,) for index in range(3))
    )
    return connection


@pytest.fixture
def safe_input(tmp_path: Path) -> Path:
    path = tmp_path / "safe.csv"
    path.write_bytes(b"PART_NO,DESCRIPTION\nA,Alpha\nB,Beta\n")
    return path


def build(connection: sqlite3.Connection, safe_input: Path):
    return build_scan_manifest(
        connection=connection,
        audit=FakeAudit(),
        repository_root=Path("."),
        artifact_type="historical_158_rehearsal_acceptance",
        input_path=safe_input,
        input_label="List_20260709_093045.csv",
        sensitive_mode=False,
        generated_at_utc="2026-09-15T00:00:00+00:00",
        repository={"commit": "1" * 40, "branch": "test", "dirty": True},
        runtime={
            "python": "3.11.9",
            "platform": "test-platform",
            "database_engine": "SQLite",
            "database_version": "3.45.1",
            "semantic_dependencies": {"numpy": "2.4.6"},
        },
    )


def test_canonical_serialization_and_request_fingerprints_are_stable():
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'
    common = dict(
        scan_mode="SAME_SITE_DUPLICATE",
        candidate_mode="group_first_primary",
        sensitive_mode=False,
        source_type="CSV",
        feature_flags={"hybrid": True},
    )
    first = request_provenance(
        selected_fields=["UNIT_MEAS", "CONTRACT"], threshold=75, **common
    )
    reordered = request_provenance(
        selected_fields=["CONTRACT", "UNIT_MEAS"], threshold=75, **common
    )
    different_threshold = request_provenance(
        selected_fields=["CONTRACT", "UNIT_MEAS"], threshold=60, **common
    )
    assert first["sha256"] == reordered["sha256"]
    assert first["sha256"] != different_threshold["sha256"]


def test_input_bytes_header_and_row_count_are_captured(safe_input: Path):
    result = input_provenance(
        input_path=safe_input,
        logical_label="safe.csv",
        row_count=2,
        canonical_s0_fingerprint="a" * 64,
        row_order_fingerprint="b" * 64,
    )
    assert result["byte_sha256"] == hashlib.sha256(safe_input.read_bytes()).hexdigest()
    assert result["byte_size"] == len(safe_input.read_bytes())
    assert result["header_sha256"] == stable_sha256(["PART_NO", "DESCRIPTION"])
    assert result["byte_hash_status"] == "AVAILABLE"


def test_unavailable_input_uses_explicit_nulls():
    result = input_provenance(
        input_path=None,
        logical_label="reconstructed-canonical-input",
        row_count=2,
        canonical_s0_fingerprint="a" * 64,
        row_order_fingerprint="b" * 64,
    )
    assert result["byte_hash_status"] == "NOT_AVAILABLE"
    assert result["byte_sha256"] is None


def test_manifest_captures_schema_request_configuration_reference_runtime_and_stages(
    safe_input: Path,
):
    connection = database()
    manifest = build(connection, safe_input)
    assert manifest["schema_version"] == SCHEMA_VERSION
    assert manifest["canonical_serialization"] == CANONICAL_SERIALIZATION
    assert manifest["repository"]["dirty"] is True
    assert manifest["request"]["selected_fields"] == ["CONTRACT", "UNIT_MEAS"]
    assert manifest["request"]["threshold"] == 75
    assert len(manifest["configuration"]["sha256"]) == 64
    reference = manifest["reference_data"]["references"][0]
    assert reference == {
        "name": "semantic_aliases",
        "schema_version": 1,
        "reference_version": "semantic-aliases-v1",
        "sha256": "0484679a78e61b2f3564c40ca7ef7f7d2b69c1a98e24d24ecdedf65eccdc4367",
    }
    assert len(manifest["runtime"]["sha256"]) == 64
    assert list(manifest["semantic_fingerprints"]) == [f"S{i}" for i in range(11)]
    assert [manifest["semantic_fingerprints"][f"S{i}"]["sha256"] for i in range(11)] == list(HISTORICAL_HASHES)


def test_manifest_captures_counts_and_zero_provider_calls(safe_input: Path):
    manifest = build(database(), safe_input)
    assert manifest["counts"] == {
        "records": 2,
        "candidate_proposals": 20492,
        "candidate_groups": 158,
        "stronger_evidence_groups": 45,
        "review_evidence_groups": 113,
        "conflicts": 27,
        "deferred": 40,
        "unassigned": 4982,
        "targeted_requests": 271,
        "candidate_partitions_explored": 171251,
        "member_rows": 3,
        "provider_calls": 0,
    }
    assert manifest["provider_calls"] == 0


def test_provider_activity_fails_the_acceptance_gate(safe_input: Path):
    with pytest.raises(ValueError, match="provider-free"):
        build(database(provider_calls=1), safe_input)


@pytest.mark.parametrize(
    "unsafe",
    (
        {"api_key": "not-even-a-real-key"},
        {"configuration": {"note": "gsk_1234567890abcdef"}},
        {"runtime": {"connection": "postgresql://user:password@example/db"}},
    ),
)
def test_secret_shaped_manifest_is_rejected_before_write(tmp_path: Path, unsafe):
    output = tmp_path / "manifest.json"
    with pytest.raises(UnsafeProvenanceError):
        write_manifest(output, unsafe)
    assert not output.exists()


def test_absolute_private_input_path_is_rejected():
    with pytest.raises(UnsafeProvenanceError, match="absolute path"):
        input_provenance(
            input_path=None,
            logical_label="C:\\private\\safe.csv",
            row_count=0,
            canonical_s0_fingerprint=None,
            row_order_fingerprint=None,
        )


def test_repository_dirty_state_does_not_serialize_status_paths(monkeypatch):
    outputs = iter(("a" * 40, "demo-authoritative-integration", "?? private-file.csv"))

    def fake_run(*_args, **_kwargs):
        return SimpleNamespace(stdout=next(outputs))

    monkeypatch.setattr("subprocess.run", fake_run)
    result = repository_provenance(Path("."))
    assert result == {
        "commit": "a" * 40,
        "branch": "demo-authoritative-integration",
        "dirty": True,
    }
    assert "private-file" not in canonical_json(result)
