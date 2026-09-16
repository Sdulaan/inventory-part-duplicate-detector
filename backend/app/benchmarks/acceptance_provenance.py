"""Versioned, secret-safe provenance manifests for acceptance artifacts only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import platform
import re
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from app.reference_data.semantic_aliases import SEMANTIC_ALIAS_REFERENCE


SCHEMA_VERSION = 1
CANONICAL_SERIALIZATION = "utf8-sorted-keys-compact-separators-v1"
RUNTIME_PACKAGES = (
    "numpy",
    "pandas",
    "scipy",
    "scikit-learn",
    "SQLAlchemy",
    "rapidfuzz",
    "openpyxl",
)
_SENSITIVE_KEYS = re.compile(
    r"(^|_)(api_?key|token|password|passwd|secret|credential|database_url|connection_string)($|_)",
    re.IGNORECASE,
)
_SENSITIVE_VALUES = (
    re.compile(r"\bgsk_[A-Za-z0-9_-]{8,}"),
    re.compile(r"\bsk-ant-[A-Za-z0-9_-]{8,}"),
    re.compile(r"\b(?:api_?key|token|password|secret)\s*=", re.IGNORECASE),
    re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://[^/@\s]+:[^/@\s]+@"),
)


class UnsafeProvenanceError(ValueError):
    """Raised before a manifest containing secret-shaped data can be written."""


def canonical_json(value: Any, *, pretty: bool = False) -> str:
    """Serialize deterministically; semantic fingerprints always use compact form."""
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    )


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _fingerprinted(payload: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    result["sha256"] = stable_sha256(payload)
    return result


def _assert_secret_safe(value: Any, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if _SENSITIVE_KEYS.search(key_text):
                raise UnsafeProvenanceError(
                    f"sensitive key rejected at {'.'.join((*path, key_text))}"
                )
            _assert_secret_safe(item, (*path, key_text))
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _assert_secret_safe(item, (*path, str(index)))
        return
    if isinstance(value, str) and any(pattern.search(value) for pattern in _SENSITIVE_VALUES):
        raise UnsafeProvenanceError(
            f"secret-shaped value rejected at {'.'.join(path) or '<root>'}"
        )


def repository_provenance(repository_root: Path) -> dict[str, Any]:
    """Capture Git identity while exposing only a dirty boolean, never path names."""
    root = repository_root.resolve()

    def git(*arguments: str) -> str:
        result = subprocess.run(
            ("git", "-C", str(root), *arguments),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return result.stdout.strip()

    return {
        "commit": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "dirty": bool(git("status", "--porcelain")),
    }


def input_provenance(
    *,
    input_path: Path | None,
    logical_label: str,
    row_count: int,
    canonical_s0_fingerprint: str | None,
    row_order_fingerprint: str | None,
) -> dict[str, Any]:
    if Path(logical_label).is_absolute() or re.match(r"^[A-Za-z]:[\\/]", logical_label):
        raise UnsafeProvenanceError("input logical label must not be an absolute path")

    result: dict[str, Any] = {
        "logical_label": logical_label,
        "row_count": row_count,
        "canonical_s0_sha256": canonical_s0_fingerprint,
        "row_order_sha256": row_order_fingerprint,
    }
    if input_path is None:
        result.update({
            "byte_size": None,
            "byte_sha256": None,
            "byte_hash_status": "NOT_AVAILABLE",
            "header_sha256": None,
        })
        return result

    content = input_path.read_bytes()
    try:
        text = content.decode("utf-8-sig")
        rows = csv.reader(io.StringIO(text))
        header = next(rows)
        parsed_row_count = sum(1 for _row in rows)
    except (UnicodeDecodeError, StopIteration, csv.Error) as exc:
        raise ValueError("acceptance input header is not a readable UTF-8 CSV") from exc
    if parsed_row_count != row_count:
        raise ValueError(
            "acceptance input row count does not match the persisted canonical scan"
        )
    result.update({
        "byte_size": len(content),
        "byte_sha256": hashlib.sha256(content).hexdigest(),
        "byte_hash_status": "AVAILABLE",
        "header_sha256": stable_sha256(header),
    })
    return result


def request_provenance(
    *,
    scan_mode: str,
    selected_fields: list[str],
    threshold: float,
    candidate_mode: str | None,
    sensitive_mode: bool | None,
    source_type: str,
    feature_flags: Mapping[str, bool],
    semantic_options: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "scan_mode": scan_mode,
        "site_scope": (
            "SAME_SITE" if scan_mode == "SAME_SITE_DUPLICATE"
            else "CROSS_SITE" if scan_mode == "CROSS_SITE_STANDARDIZATION"
            else scan_mode
        ),
        "selected_fields": sorted(set(selected_fields)),
        "threshold": float(threshold),
        "candidate_mode": candidate_mode,
        "sensitive_mode": sensitive_mode,
        "source_type": source_type,
        "feature_flags": dict(sorted(feature_flags.items())),
        "semantic_options": dict(sorted((semantic_options or {}).items())),
    }
    return _fingerprinted(payload)


def reference_data_provenance() -> dict[str, Any]:
    references = [{
        "name": "semantic_aliases",
        "schema_version": SEMANTIC_ALIAS_REFERENCE.schema_version,
        "reference_version": SEMANTIC_ALIAS_REFERENCE.reference_version,
        "sha256": SEMANTIC_ALIAS_REFERENCE.fingerprint,
    }]
    return {
        "references": references,
        "sha256": stable_sha256(references),
    }


def runtime_provenance() -> dict[str, Any]:
    dependencies = {
        name: importlib.metadata.version(name)
        for name in RUNTIME_PACKAGES
    }
    semantic_bundle = {
        "python": platform.python_version(),
        "sqlite": sqlite3.sqlite_version,
        "dependencies": dependencies,
    }
    return {
        "python": semantic_bundle["python"],
        "platform": platform.platform(),
        "database_engine": "SQLite",
        "database_version": semantic_bundle["sqlite"],
        "semantic_dependencies": dependencies,
        "sha256": stable_sha256(semantic_bundle),
    }


def _one(connection: sqlite3.Connection, table: str, scan_id: int) -> sqlite3.Row:
    rows = list(connection.execute(f"select * from {table} where scan_id=?", (scan_id,)))
    if len(rows) != 1:
        raise ValueError(f"expected one {table} row for scan {scan_id}, found {len(rows)}")
    return rows[0]


def build_scan_manifest(
    *,
    connection: sqlite3.Connection,
    audit: Any,
    repository_root: Path,
    artifact_type: str,
    input_path: Path | None,
    input_label: str,
    sensitive_mode: bool | None = None,
    generated_at_utc: str | None = None,
    repository: Mapping[str, Any] | None = None,
    runtime: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one manifest from persisted acceptance data without mutating it."""
    scan_id = audit.scan_id
    scan = connection.execute(
        "select * from duplicate_scan where id=?", (scan_id,)
    ).fetchone()
    if scan is None:
        raise ValueError(f"scan {scan_id} does not exist")
    discovery = _one(connection, "identity_discovery_run", scan_id)
    evidence = _one(connection, "identity_evidence_run", scan_id)
    resolution = _one(connection, "identity_resolution_run", scan_id)
    projection = _one(connection, "g2_v2_projection_run", scan_id)
    orchestration = _one(connection, "scan_orchestration_run", scan_id)
    stages = audit.stages()
    stage_fingerprints = {
        item.stage.split("_", 1)[0]: {
            "name": item.stage,
            "count": item.count,
            "sha256": item.fingerprint,
        }
        for item in stages
    }
    if set(stage_fingerprints) != {f"S{index}" for index in range(11)}:
        raise ValueError("acceptance manifest requires distinct S0-S10 stages")

    discovery_configuration = json.loads(discovery["configuration_json"])
    resolution_configuration = json.loads(resolution["configuration_json"])
    selected_fields = json.loads(scan["selected_fields"])
    request = request_provenance(
        scan_mode=scan["scan_mode"],
        selected_fields=selected_fields,
        threshold=scan["threshold"],
        candidate_mode=orchestration["mode"],
        sensitive_mode=sensitive_mode,
        source_type=scan["source_type"],
        feature_flags={
            "hybrid_retrieval_enabled": bool(
                discovery_configuration.get("hybrid_enabled", False)
            ),
            "local_embedding_enabled": bool(
                discovery_configuration.get("local_embedding_enabled", False)
            ),
        },
        semantic_options={
            "identity_discovery_mode": discovery_configuration.get("scan_mode"),
            "visible_projection_contract": orchestration["visible_projection_contract"],
        },
    )
    configuration_payload = {
        "orchestration": {
            "mode": orchestration["mode"],
            "policy_version": orchestration["policy_version"],
            "policy_sha256": orchestration["policy_fingerprint"],
            "primary_identity_pipeline": orchestration["primary_identity_pipeline"],
            "visible_projection_contract": orchestration["visible_projection_contract"],
        },
        "discovery": {
            "algorithm_version": discovery["algorithm_version"],
            "configuration_version": discovery["configuration_version"],
            "normalization_version": discovery["normalization_version"],
            "configuration": discovery_configuration,
        },
        "evidence": {
            "algorithm_version": evidence["algorithm_version"],
            "configuration_sha256": evidence["configuration_fingerprint"],
        },
        "resolution": {
            "algorithm_version": resolution["resolver_algorithm_version"],
            "configuration_version": resolution["configuration_version"],
            "configuration_sha256": resolution["configuration_fingerprint"],
            "configuration": resolution_configuration,
        },
        "projection": {
            "adapter_algorithm_version": projection["adapter_algorithm_version"],
            "adapter_configuration_sha256": projection["adapter_configuration_fingerprint"],
            "snapshot_contract_version": projection["snapshot_contract_version"],
        },
        "cache": {
            "key_namespace": "semantic-text-fingerprint-plus-model-version",
            "embedding_model_version": discovery_configuration.get("local_embedding_model"),
            "representation": "float64-round-7-decimals-to-float32",
        },
    }
    configuration = _fingerprinted(configuration_payload)
    references = reference_data_provenance()
    runtime_payload = dict(runtime or runtime_provenance())
    if "sha256" not in runtime_payload:
        runtime_payload["sha256"] = stable_sha256(runtime_payload)

    provider_counts = [
        int(discovery["provider_request_count"]),
        int(resolution["provider_request_count"]),
    ]
    hybrid = connection.execute(
        "select provider_request_count from hybrid_retrieval_run where scan_id=?",
        (scan_id,),
    ).fetchone()
    if hybrid is not None:
        provider_counts.append(int(hybrid["provider_request_count"]))
    provider_calls = sum(provider_counts)
    if provider_calls != 0:
        raise ValueError("acceptance provenance requires a provider-free scan")

    counts = {
        "records": int(resolution["source_record_count"]),
        "candidate_proposals": int(discovery["proposal_count"]),
        "candidate_groups": int(resolution["accepted_group_count"]),
        "stronger_evidence_groups": int(resolution["likely_group_count"]),
        "review_evidence_groups": int(resolution["review_group_count"]),
        "conflicts": int(resolution["conflict_count"]),
        "deferred": int(resolution["deferred_work_unit_count"]),
        "unassigned": int(resolution["unassigned_record_count"]),
        "targeted_requests": int(resolution["targeted_evidence_request_count"]),
        "candidate_partitions_explored": int(resolution["candidate_partitions_explored"]),
        "member_rows": int(connection.execute(
            "select count(*) from g2_v2_group_member where projection_run_id=?",
            (projection["id"],),
        ).fetchone()[0]),
        "provider_calls": provider_calls,
    }
    row_order = [
        [row["source_row_index"], row["source_record_fingerprint"]]
        for row in audit.records
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "canonical_serialization": CANONICAL_SERIALIZATION,
        "artifact_type": artifact_type,
        "generated_at_utc": generated_at_utc or datetime.now(timezone.utc).isoformat(),
        "repository": dict(repository or repository_provenance(repository_root)),
        "input": input_provenance(
            input_path=input_path,
            logical_label=input_label,
            row_count=stages[0].count,
            canonical_s0_fingerprint=stages[0].fingerprint,
            row_order_fingerprint=stable_sha256(row_order),
        ),
        "request": request,
        "configuration": configuration,
        "reference_data": references,
        "runtime": runtime_payload,
        "semantic_fingerprints": stage_fingerprints,
        "counts": counts,
        "provider_calls": provider_calls,
    }
    _assert_secret_safe(manifest)
    return manifest


def write_manifest(path: Path, manifest: Mapping[str, Any]) -> None:
    """Fail closed on unsafe content and propagate write failures to acceptance."""
    _assert_secret_safe(manifest)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(dict(manifest), pretty=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--scan-id", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--artifact-type", required=True)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--input-label", required=True)
    parser.add_argument(
        "--sensitive-mode", choices=("true", "false", "not-recorded"),
        default="not-recorded",
    )
    args = parser.parse_args()

    connection = sqlite3.connect(f"file:{args.database.resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        from app.benchmarks.scan_determinism_audit import ScanAudit

        audit = ScanAudit(connection, args.scan_id)
        sensitive_mode = {
            "true": True,
            "false": False,
            "not-recorded": None,
        }[args.sensitive_mode]
        manifest = build_scan_manifest(
            connection=connection,
            audit=audit,
            repository_root=args.repository_root,
            artifact_type=args.artifact_type,
            input_path=args.input,
            input_label=args.input_label,
            sensitive_mode=sensitive_mode,
        )
        write_manifest(args.output, manifest)
        print(canonical_json(manifest, pretty=True))
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
