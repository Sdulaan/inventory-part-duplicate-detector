"""Read-only, stable-identity comparison of two persisted scan pipelines.

This module is diagnostic-only.  It deliberately uses source-row identity plus
the immutable source-record fingerprint instead of scan-local primary keys and
record references.  It never imports runtime configuration or provider code.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


NON_SEMANTIC_RECORD_COLUMNS = {"id", "scan_id", "record_ref_key", "created_at"}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def fingerprint(items: Iterable[Any]) -> str:
    encoded = canonical_json(sorted(canonical_json(item) for item in items)).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def canonical_pair(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))


@dataclass(frozen=True)
class StageResult:
    stage: str
    count: int
    fingerprint: str
    items: tuple[Any, ...]


def stage_result(stage: str, items: Iterable[Any]) -> StageResult:
    materialized = tuple(items)
    return StageResult(stage, len(materialized), fingerprint(materialized), materialized)


class ScanAudit:
    def __init__(self, connection: sqlite3.Connection, scan_id: int):
        self.connection = connection
        self.scan_id = scan_id
        self.records = self._rows(
            "select * from scan_record_snapshot where scan_id=? order by source_row_index, id",
            (scan_id,),
        )
        self.record_by_id = {row["id"]: row for row in self.records}
        self.stable_by_id = {row["id"]: self._stable_record_key(row) for row in self.records}
        self.stable_by_ref = {
            row["record_ref_key"]: self._stable_record_key(row) for row in self.records
        }
        self.discovery_run = self._one("identity_discovery_run")
        self.evidence_run = self._one("identity_evidence_run")
        self.resolution_run = self._one("identity_resolution_run")
        self.projection_run = self._one("g2_v2_projection_run")
        evidence_rows = self._rows(
            "select * from identity_evidence_edge_snapshot where evidence_run_id=?",
            (self.evidence_run["id"],),
        )
        self.semantic_by_evidence_reference = {
            row["evidence_fingerprint"]: {
                "pair": self._pair(row),
                "edge_class": row["edge_class"],
                "reason_codes": self._json(row["classification_reason_codes_json"]),
            }
            for row in evidence_rows
        }
        targeted_rows = self._rows(
            "select * from identity_resolution_targeted_evidence "
            "where resolution_run_id=? and evaluation_completed=1",
            (self.resolution_run["id"],),
        )
        self.semantic_by_evidence_reference.update({
            row["evidence_fingerprint"]: {
                "pair": canonical_pair(
                    self.stable_by_id[row["record_id_1"]],
                    self.stable_by_id[row["record_id_2"]],
                ),
                "edge_class": row["edge_class"],
                "reason_codes": self._json(row["reason_codes_json"]),
                "generic_only": bool(row["generic_only"]),
            }
            for row in targeted_rows
            if row["evidence_fingerprint"]
        })

    def _rows(self, sql: str, parameters: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        return list(self.connection.execute(sql, parameters))

    def _one(self, table: str) -> sqlite3.Row:
        rows = self._rows(f"select * from {table} where scan_id=?", (self.scan_id,))
        if len(rows) != 1:
            raise ValueError(f"expected one {table} row for scan {self.scan_id}, found {len(rows)}")
        return rows[0]

    @staticmethod
    def _stable_record_key(row: sqlite3.Row) -> str:
        return f"row:{row['source_row_index']}:{row['source_record_fingerprint']}"

    @staticmethod
    def _json(raw: Any) -> Any:
        if raw in (None, ""):
            return None
        if not isinstance(raw, str):
            return raw
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    def _normalize_refs(self, value: Any) -> Any:
        if isinstance(value, str):
            return self.stable_by_ref.get(
                value, self.semantic_by_evidence_reference.get(value, value)
            )
        if isinstance(value, list):
            return [self._normalize_refs(item) for item in value]
        if isinstance(value, dict):
            normalized = {}
            for key, item in value.items():
                if key.endswith("record_ids") and isinstance(item, list):
                    normalized[key] = [self.stable_by_id[record_id] for record_id in item]
                elif key.endswith("_pairs") and isinstance(item, list):
                    normalized[key] = [
                        canonical_pair(
                            self.stable_by_id[pair[0]], self.stable_by_id[pair[1]]
                        )
                        for pair in item
                    ]
                else:
                    normalized[key] = self._normalize_refs(item)
            return normalized
        return value

    def _pair(self, row: sqlite3.Row) -> tuple[str, str]:
        return canonical_pair(
            self.stable_by_id[row["record_id_1"]],
            self.stable_by_id[row["record_id_2"]],
        )

    def s0_records(self) -> StageResult:
        items = []
        for row in self.records:
            item = {
                key: row[key]
                for key in row.keys()
                if key not in NON_SEMANTIC_RECORD_COLUMNS
            }
            items.append(item)
        return stage_result("S0_CANONICAL_RECORD_SNAPSHOTS", items)

    def proposals(self) -> tuple[dict[str, Any], ...]:
        rows = self._rows(
            "select * from identity_neighbor_proposal where discovery_run_id=?",
            (self.discovery_run["id"],),
        )
        return tuple({
            "pair": self._pair(row),
            "source_channels": self._json(row["source_channels_json"]),
            "channel_provenance": self._json(row["channel_provenance_json"]),
            "reciprocal_channels": self._json(row["reciprocal_channels_json"]),
            "proposal_priority": row["proposal_priority"],
            "proposal_order": row["proposal_order"],
            "discovery_context": self._normalize_refs(
                self._json(row["discovery_context_json"])
            ),
            "truncated": bool(row["truncated"]),
            "degraded": bool(row["degraded"]),
        } for row in rows)

    def evidence(self, *, classification: bool) -> tuple[dict[str, Any], ...]:
        rows = self._rows(
            "select * from identity_evidence_edge_snapshot where evidence_run_id=?",
            (self.evidence_run["id"],),
        )
        items = []
        for row in rows:
            item = {
                "pair": self._pair(row),
                "deterministic_score": row["deterministic_score"],
                "component_scores": self._json(row["component_scores_json"]),
                "protected_conflicts": self._json(row["protected_conflicts_json"]),
                "generic_evidence": self._json(row["generic_evidence_json"]),
                "technical_evidence": self._json(row["technical_evidence_json"]),
                "uom_context": self._json(row["uom_context_json"]),
                "evaluation_context": self._normalize_refs(
                    self._json(row["evaluation_context_json"])
                ),
            }
            if classification:
                item.update({
                    "edge_class": row["edge_class"],
                    "reason_codes": self._json(row["classification_reason_codes_json"]),
                    "rule_decision": row["rule_decision"],
                    "rejection_reason": row["rejection_reason"],
                    "evaluation_algorithm_version": row["evaluation_algorithm_version"],
                })
            items.append(item)
        return tuple(items)

    def neighborhoods(self) -> tuple[dict[str, Any], ...]:
        rows = self._rows(
            "select * from identity_neighborhood_snapshot where discovery_run_id=?",
            (self.discovery_run["id"],),
        )
        members = self._rows(
            "select m.* from identity_neighborhood_member m "
            "join identity_neighborhood_snapshot n on n.id=m.neighborhood_id "
            "where n.discovery_run_id=? order by m.neighborhood_id, m.member_order",
            (self.discovery_run["id"],),
        )
        by_neighborhood: dict[int, list[sqlite3.Row]] = defaultdict(list)
        for member in members:
            by_neighborhood[member["neighborhood_id"]].append(member)
        return tuple({
            "anchor": self.stable_by_id[row["anchor_record_id"]],
            "ordered_members": [
                self.stable_by_id[member["record_id"]]
                for member in by_neighborhood[row["id"]]
            ],
            "candidate_neighbor_count": row["candidate_neighbor_count"],
            "included_neighbor_count": row["included_neighbor_count"],
            "is_truncated": bool(row["is_truncated"]),
            "degraded": bool(row["degraded"]),
            "warning_codes": self._json(row["warning_codes_json"]),
            "configuration_fingerprint": row["configuration_fingerprint"],
        } for row in rows)

    def resolution_inputs(self) -> tuple[dict[str, Any], ...]:
        constraints = self._rows(
            "select * from identity_resolution_constraint_input where resolution_run_id=?",
            (self.resolution_run["id"],),
        )
        run = self.resolution_run
        return ({
            "configuration_version": run["configuration_version"],
            "configuration_fingerprint": run["configuration_fingerprint"],
            "configuration": self._json(run["configuration_json"]),
            "work_unit_count": run["work_unit_count"],
            "candidate_partitions_explored": run["candidate_partitions_explored"],
            "targeted_evidence_request_count": run["targeted_evidence_request_count"],
            "effective_constraints": [{
                "pair": self._pair(row),
                "constraint_type": row["constraint_type"],
                "source_authority": row["source_authority"],
            } for row in constraints],
        },)

    def _member_collections(
        self,
        snapshot_table: str,
        member_table: str,
        parent_column: str,
        run_column: str,
        run_id: int,
        extra_columns: tuple[str, ...],
    ) -> tuple[dict[str, Any], ...]:
        snapshots = self._rows(
            f"select * from {snapshot_table} where {run_column}=?", (run_id,)
        )
        members = self._rows(
            f"select * from {member_table} where {run_column}=?", (run_id,)
        )
        grouped: dict[int, list[sqlite3.Row]] = defaultdict(list)
        for member in members:
            grouped[member[parent_column]].append(member)
        items = []
        for row in snapshots:
            member_rows = grouped[row["id"]]
            stable_members = sorted(
                self.stable_by_id[member["record_id"]] for member in member_rows
            )
            item: dict[str, Any] = {"members": stable_members}
            for column in extra_columns:
                value = row[column]
                if column.endswith("_json"):
                    value = self._normalize_refs(self._json(value))
                if column == "protected_evidence_references_json":
                    value = sorted(value, key=canonical_json)
                item[column] = value
            items.append(item)
        return tuple(items)

    def resolution_groups(self) -> tuple[dict[str, Any], ...]:
        return self._member_collections(
            "identity_resolution_group_snapshot", "identity_resolution_group_member",
            "group_snapshot_id", "resolution_run_id", self.resolution_run["id"],
            ("status", "validation_mode", "evidence_summary_json",
             "bridge_risk_summary_json", "genericity_risk_summary_json",
             "missing_evidence_summary_json"),
        )

    def conflicts(self) -> tuple[dict[str, Any], ...]:
        return self._member_collections(
            "identity_resolution_conflict_snapshot", "identity_resolution_conflict_member",
            "conflict_snapshot_id", "resolution_run_id", self.resolution_run["id"],
            ("conflict_type", "summary", "protected_evidence_references_json"),
        )

    def deferred(self) -> tuple[dict[str, Any], ...]:
        return self._member_collections(
            "identity_resolution_deferred_snapshot", "identity_resolution_deferred_member",
            "deferred_snapshot_id", "resolution_run_id", self.resolution_run["id"],
            ("reason", "unfinished_evidence_summary"),
        )

    def unassigned(self) -> tuple[str, ...]:
        rows = self._rows(
            "select record_id from identity_resolution_unassigned_record "
            "where resolution_run_id=?", (self.resolution_run["id"],),
        )
        return tuple(self.stable_by_id[row["record_id"]] for row in rows)

    def projection_groups(self) -> tuple[dict[str, Any], ...]:
        return self._member_collections(
            "g2_v2_group_snapshot", "g2_v2_group_member", "group_snapshot_id",
            "projection_run_id", self.projection_run["id"],
            ("status", "validation_mode", "group_evidence_summary_json",
             "bridge_risk_summary_json", "genericity_risk_summary_json",
             "missing_evidence_summary_json", "validation_coverage_json"),
        )

    def stages(self) -> tuple[StageResult, ...]:
        return (
            self.s0_records(),
            stage_result("S1_CANDIDATE_DISCOVERY_PROPOSALS", self.proposals()),
            stage_result("S2_DETERMINISTIC_EVIDENCE_INPUTS", self.evidence(classification=False)),
            stage_result("S3_GF4_CLASSIFIED_EVIDENCE_EDGES", self.evidence(classification=True)),
            stage_result("S4_GF5_ELIGIBLE_NEIGHBORHOODS", self.neighborhoods()),
            stage_result("S5_GF5_OBJECTIVE_INPUTS", self.resolution_inputs()),
            stage_result("S6_GF5_SELECTED_GROUPS", self.resolution_groups()),
            stage_result("S7_GF5_CONFLICTS", self.conflicts()),
            stage_result("S8_GF5_DEFERRED", self.deferred()),
            stage_result("S9_GF5_UNASSIGNED", self.unassigned()),
            stage_result("S10_G2_V2_GROUP_PROJECTION", self.projection_groups()),
        )


def _member_key(group: dict[str, Any]) -> tuple[str, ...]:
    return tuple(group["members"])


def _source_rows(member_key: tuple[str, ...]) -> str:
    return ";".join(item.split(":", 2)[1] for item in member_key)


def run_audit(
    database_path: Path,
    scan_a: int,
    scan_b: int,
    output_directory: Path,
    *,
    input_path: Path | None = None,
    input_label: str = "INPUT_NOT_RECORDED",
    repository_root: Path | None = None,
    sensitive_mode: bool | None = None,
) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{database_path.resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        left = ScanAudit(connection, scan_a)
        right = ScanAudit(connection, scan_b)
        left_stages = left.stages()
        right_stages = right.stages()
        stage_rows = [{
            "stage": a.stage,
            f"scan_{scan_a}_count": a.count,
            f"scan_{scan_a}_hash": a.fingerprint,
            f"scan_{scan_b}_count": b.count,
            f"scan_{scan_b}_hash": b.fingerprint,
            "equal": a.fingerprint == b.fingerprint,
        } for a, b in zip(left_stages, right_stages, strict=True)]

        left_groups = {_member_key(item): item for item in left.projection_groups()}
        right_groups = {_member_key(item): item for item in right.projection_groups()}
        only_left = sorted(left_groups.keys() - right_groups.keys())
        only_right = sorted(right_groups.keys() - left_groups.keys())
        common = sorted(left_groups.keys() & right_groups.keys())

        output_directory.mkdir(parents=True, exist_ok=True)
        summary = {
            "scan_a": scan_a,
            "scan_b": scan_b,
            "input_bytes_equal": "NOT_PERSISTED_NOT_DIRECTLY_VERIFIABLE",
            "input_rows_equal": left.s0_records().count == right.s0_records().count,
            "input_row_order_equal": [
                (row["source_row_index"], row["source_record_fingerprint"])
                for row in left.records
            ] == [
                (row["source_row_index"], row["source_record_fingerprint"])
                for row in right.records
            ],
            "canonical_record_snapshots_equal": (
                left.s0_records().fingerprint == right.s0_records().fingerprint
            ),
            "stages": stage_rows,
            "groups": {
                f"scan_{scan_a}_only": len(only_left),
                f"scan_{scan_b}_only": len(only_right),
                "common": len(common),
                "common_status_changed": sum(
                    left_groups[key]["status"] != right_groups[key]["status"]
                    for key in common
                ),
            },
        }
        (output_directory / "scan34_35_stage_fingerprints.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        with (output_directory / "scan34_35_group_diff.csv").open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=("scope", "status", "source_rows"))
            writer.writeheader()
            for scope, keys, groups in (
                (f"scan_{scan_a}_only", only_left, left_groups),
                (f"scan_{scan_b}_only", only_right, right_groups),
                ("common", common, left_groups),
            ):
                for key in keys:
                    writer.writerow({
                        "scope": scope,
                        "status": groups[key]["status"],
                        "source_rows": _source_rows(key),
                    })

        proposal_indexes = []
        evidence_indexes = []
        for audit in (left, right):
            proposal_indexes.append({tuple(item["pair"]): item for item in audit.proposals()})
            evidence_indexes.append({tuple(item["pair"]): item for item in audit.evidence(classification=True)})
        with (output_directory / "scan34_35_changed_family_trace.csv").open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            fields = (
                "group_scope", "group_status", "group_source_rows", "pair_source_rows",
                f"scan_{scan_a}_proposed", f"scan_{scan_b}_proposed",
                f"scan_{scan_a}_channels", f"scan_{scan_b}_channels",
                f"scan_{scan_a}_gf4_class", f"scan_{scan_b}_gf4_class",
                f"scan_{scan_a}_score", f"scan_{scan_b}_score",
            )
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for scope, keys, groups in (
                (f"scan_{scan_a}_only", only_left, left_groups),
                (f"scan_{scan_b}_only", only_right, right_groups),
            ):
                for key in keys:
                    for pair in itertools.combinations(key, 2):
                        canonical = canonical_pair(*pair)
                        proposals = [index.get(canonical) for index in proposal_indexes]
                        evidence = [index.get(canonical) for index in evidence_indexes]
                        writer.writerow({
                            "group_scope": scope,
                            "group_status": groups[key]["status"],
                            "group_source_rows": _source_rows(key),
                            "pair_source_rows": _source_rows(canonical),
                            f"scan_{scan_a}_proposed": proposals[0] is not None,
                            f"scan_{scan_b}_proposed": proposals[1] is not None,
                            f"scan_{scan_a}_channels": canonical_json(proposals[0]["source_channels"]) if proposals[0] else "",
                            f"scan_{scan_b}_channels": canonical_json(proposals[1]["source_channels"]) if proposals[1] else "",
                            f"scan_{scan_a}_gf4_class": evidence[0]["edge_class"] if evidence[0] else "",
                            f"scan_{scan_b}_gf4_class": evidence[1]["edge_class"] if evidence[1] else "",
                            f"scan_{scan_a}_score": evidence[0]["deterministic_score"] if evidence[0] else "",
                            f"scan_{scan_b}_score": evidence[1]["deterministic_score"] if evidence[1] else "",
                        })

        with (output_directory / "scan34_35_rerun_matrix.csv").open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            fields = ("scan_id",) + tuple(item.stage for item in left_stages)
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerow({"scan_id": scan_a, **{item.stage: item.fingerprint for item in left_stages}})
            writer.writerow({"scan_id": scan_b, **{item.stage: item.fingerprint for item in right_stages}})

        # Acceptance provenance is deliberately an artifact-side concern.  A
        # write or validation failure propagates and fails this diagnostic gate;
        # ordinary production scans never import or invoke the writer.
        from app.benchmarks.acceptance_provenance import (
            build_scan_manifest,
            write_manifest,
        )

        repo = repository_root or Path(__file__).resolve().parents[3]
        for audit in (left, right):
            manifest = build_scan_manifest(
                connection=connection,
                audit=audit,
                repository_root=repo,
                artifact_type="scan_determinism_acceptance",
                input_path=input_path,
                input_label=input_label,
                sensitive_mode=sensitive_mode,
            )
            write_manifest(
                output_directory
                / f"scan_{audit.scan_id}.acceptance_provenance.json",
                manifest,
            )
        return summary
    finally:
        connection.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--scan-a", type=int, default=34)
    parser.add_argument("--scan-b", type=int, default=35)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--input-label", default="INPUT_NOT_RECORDED")
    parser.add_argument("--repository-root", type=Path)
    parser.add_argument(
        "--sensitive-mode", choices=("true", "false", "not-recorded"),
        default="not-recorded",
    )
    args = parser.parse_args()
    sensitive_mode = {
        "true": True,
        "false": False,
        "not-recorded": None,
    }[args.sensitive_mode]
    result = run_audit(
        args.database,
        args.scan_a,
        args.scan_b,
        args.output_directory,
        input_path=args.input,
        input_label=args.input_label,
        repository_root=args.repository_root,
        sensitive_mode=sensitive_mode,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
