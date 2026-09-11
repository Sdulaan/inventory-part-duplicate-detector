"""Tests for the read-only Scan 34/35 reproducibility diagnostic."""

import csv
from pathlib import Path

import numpy as np
from sklearn.preprocessing import normalize

from app.benchmarks.scan_determinism_audit import (
    canonical_pair,
    fingerprint,
    stage_result,
)
from app.services.canonical_record_service import canonical_record_ref_key
from app.services.character_retrieval import (
    CharacterLshConfiguration,
    retrieve_lsh_directed_neighbors,
)


GROUP_DIFF = (
    Path(__file__).resolve().parents[2]
    / "artifacts"
    / "scan34_35_determinism"
    / "scan34_35_group_diff.csv"
)


def test_diagnostic_fingerprint_ignores_collection_order_but_not_content():
    first = ({"pair": ("row-1", "row-2"), "score": 75.0}, {"pair": ("row-3", "row-4")})
    assert fingerprint(first) == fingerprint(reversed(first))
    assert fingerprint(first) != fingerprint(first[:1])


def test_stage_result_preserves_count_and_uses_canonical_pair_order():
    items = ({"pair": canonical_pair("z", "a")}, {"pair": canonical_pair("b", "c")})
    result = stage_result("S1", items)
    assert result.count == 2
    assert result.items[0]["pair"] == ("a", "z")
    assert len(result.fingerprint) == 64


def test_characterization_scan_local_reference_changes_a_tied_retrieval_decision():
    """Current behavior: scan ID leaks into a decision-affecting tie key.

    This is a passing characterization of the diagnosed defect, not a fix.  The
    next correction should replace the scan-local tie identity and invert this
    expectation.
    """
    matrix = np.zeros((4, 384), dtype=np.float32)
    matrix[:, 0] = 1.0
    matrix = normalize(matrix)
    configuration = CharacterLshConfiguration(
        table_count=4,
        bits_per_table=2,
        probe_radius=2,
        candidate_pool_k=3,
    )

    chosen = []
    for scan_id in (34, 35):
        refs = tuple(canonical_record_ref_key(scan_id, row) for row in range(4))
        result = retrieve_lsh_directed_neighbors(matrix, refs, 1, configuration)
        chosen.append(result.directed_neighbors[0][0][0])

    assert chosen == [1, 3]


def test_characterization_is_repeatable_when_reference_identity_is_stable():
    matrix = normalize(np.random.default_rng(1101).random((24, 384), dtype=np.float32))
    refs = tuple(f"source-row-{row:05d}" for row in range(24))
    configuration = CharacterLshConfiguration(
        table_count=4,
        bits_per_table=2,
        probe_radius=2,
        candidate_pool_k=23,
    )

    runs = [retrieve_lsh_directed_neighbors(matrix, refs, 3, configuration) for _ in range(3)]
    semantic = [
        tuple(sorted(
            (source, target, round(score, 8))
            for source, neighbors in result.directed_neighbors.items()
            for target, score in neighbors
        ))
        for result in runs
    ]
    assert semantic[0] == semantic[1] == semantic[2]


def test_changed_group_fixture_covers_both_tiers_on_both_sides():
    with GROUP_DIFF.open(newline="", encoding="utf-8") as handle:
        changed = [
            row for row in csv.DictReader(handle)
            if row["scope"] in {"scan_34_only", "scan_35_only"}
        ]

    observed = {(row["scope"], row["status"]) for row in changed}
    assert observed == {
        ("scan_34_only", "LIKELY_DUPLICATE_GROUP"),
        ("scan_34_only", "POSSIBLE_DUPLICATE_GROUP_REVIEW"),
        ("scan_35_only", "LIKELY_DUPLICATE_GROUP"),
        ("scan_35_only", "POSSIBLE_DUPLICATE_GROUP_REVIEW"),
    }
    assert all(row["source_rows"] for row in changed)
