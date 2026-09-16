"""Diagnostic fixture for the Duplicate Checking Conditions semantics audit.

This test records existing Group-First behavior; it does not prescribe or alter
the product semantics.
"""

import json
from itertools import combinations

import pandas as pd

from app.core.config import Settings
from app.db.models import (
    G2V2GroupMemberRow,
    G2V2GroupSnapshotRow,
    IdentityEvidenceEdgeSnapshot,
    IdentityNeighborProposal,
    IdentityResolutionDeferredSnapshot,
    IdentityResolutionRun,
    IdentityResolutionUnassignedRecord,
    ScanRecordSnapshot,
)
from app.services.scan_runner import ScanRunner


ROWS = pd.DataFrame([
    {
        "PART_NO": "SKU-A101",
        "DESCRIPTION": "Industrial roller bearing 6205 ZZ C3",
        "CONTRACT": "ST001",
        "UNIT_MEAS": "PCS",
    },
    {
        "PART_NO": "SKU-B202",
        "DESCRIPTION": "Industrial roller bearing 6205 ZZ C3",
        "CONTRACT": "ST001",
        "UNIT_MEAS": "PCS",
    },
    {
        "PART_NO": "SKU-C303",
        "DESCRIPTION": "Industrial roller bearing 6205 ZZ C3",
        "CONTRACT": "ST002",
        "UNIT_MEAS": "PCS",
    },
    {
        "PART_NO": "SKU-D404",
        "DESCRIPTION": "Industrial roller bearing 6205 ZZ C3",
        "CONTRACT": "ST001",
        "UNIT_MEAS": "KG",
    },
])


def _configuration():
    return Settings(
        llm_provider="none",
        llm_demo_enabled=False,
        identity_orchestration_mode="group_first_primary",
        group_first_shadow_comparison_enabled=False,
        hybrid_retrieval_enabled=True,
        local_embedding_enabled=False,
        hybrid_retrieval_lexical_top_k=10,
        hybrid_retrieval_vector_top_k=10,
        hybrid_retrieval_final_top_k=10,
        hybrid_retrieval_max_pairs_per_scan=100,
        hybrid_retrieval_family_max=30,
        hybrid_retrieval_tier_a_max=100,
        hybrid_retrieval_tier_b_max=100,
        hybrid_retrieval_tier_c_max=100,
        identity_neighborhood_max_members=20,
    )


def _pair_labels(rows, left_id, right_id):
    labels = {row.id: chr(ord("A") + row.source_row_index) for row in rows}
    return "".join(sorted((labels[left_id], labels[right_id])))


def _run_case(db, selected_fields):
    scan, _ = ScanRunner(db, _configuration()).run(
        ROWS.copy(),
        f"condition semantics {','.join(selected_fields) or 'none'}",
        selected_fields,
        75,
        scan_mode="SAME_SITE_DUPLICATE",
        orchestration_mode="group_first_primary",
    )
    records = db.query(ScanRecordSnapshot).filter_by(scan_id=scan.id).all()
    proposals = db.query(IdentityNeighborProposal).filter_by(scan_id=scan.id).all()
    evidence = db.query(IdentityEvidenceEdgeSnapshot).filter_by(scan_id=scan.id).all()
    resolution = db.query(IdentityResolutionRun).filter_by(scan_id=scan.id).one()
    deferred = (
        db.query(IdentityResolutionDeferredSnapshot).filter_by(scan_id=scan.id).all()
    )
    unassigned = (
        db.query(IdentityResolutionUnassignedRecord).filter_by(scan_id=scan.id).all()
    )
    groups = db.query(G2V2GroupSnapshotRow).filter_by(scan_id=scan.id).all()
    members = db.query(G2V2GroupMemberRow).filter_by(scan_id=scan.id).all()
    return {
        "proposal_pairs": sorted(
            _pair_labels(records, row.record_id_1, row.record_id_2)
            for row in proposals
        ),
        "evidence": {
            _pair_labels(records, row.record_id_1, row.record_id_2): {
                "class": row.edge_class,
                "score": row.deterministic_score,
            }
            for row in evidence
        },
        "candidate_partitions_explored": resolution.candidate_partitions_explored,
        "deferred_reasons": sorted(row.reason for row in deferred),
        "unassigned": sorted(
            chr(
                ord("A")
                + next(
                    record.source_row_index
                    for record in records
                    if record.id == row.record_id
                )
            )
            for row in unassigned
        ),
        "groups": sorted(
            sorted(
                chr(
                    ord("A")
                    + next(
                        record.source_row_index
                        for record in records
                        if record.id == member.record_id
                    )
                )
                for member in members
                if member.group_snapshot_id == group.id
            )
            for group in groups
        ),
    }


def test_four_case_duplicate_condition_semantics_are_observed_without_providers(
    db, monkeypatch,
):
    def provider_called(*_args, **_kwargs):
        raise AssertionError("semantics audit invoked a provider")

    monkeypatch.setattr("app.llm.factory.create_llm_provider", provider_called)
    monkeypatch.setattr(
        "app.llm.groq_group_provider.create_group_advisory_provider", provider_called
    )

    cases = {
        "none": _run_case(db, []),
        "contract": _run_case(db, ["CONTRACT"]),
        "uom": _run_case(db, ["UNIT_MEAS"]),
        "contract_uom": _run_case(db, ["CONTRACT", "UNIT_MEAS"]),
    }
    all_pairs = sorted("".join(pair) for pair in combinations("ABCD", 2))
    assert cases["none"]["proposal_pairs"] == all_pairs
    assert cases["uom"]["proposal_pairs"] == all_pairs
    assert cases["contract"]["proposal_pairs"] == ["AB", "AD", "BD"]
    assert cases["contract_uom"]["proposal_pairs"] == ["AB", "AD", "BD"]
    assert cases["none"]["groups"] == cases["uom"]["groups"] == []
    assert cases["contract"]["groups"] == [["A", "B", "D"]]
    assert cases["contract_uom"]["groups"] == [["A", "B", "D"]]
    assert cases["none"]["unassigned"] == cases["uom"]["unassigned"] == [
        "A", "B", "C", "D",
    ]
    assert cases["contract"]["unassigned"] == ["C"]
    assert cases["contract_uom"]["unassigned"] == ["C"]
    expected_scores = {
        "none": dict.fromkeys(all_pairs, 85.71),
        "contract": {
            "AB": 95.71,
            "AD": 95.71,
            "BD": 95.71,
        },
        "uom": {
            "AB": 95.71,
            "AC": 95.71,
            "AD": 75.71,
            "BC": 95.71,
            "BD": 75.71,
            "CD": 75.71,
        },
        "contract_uom": {
            "AB": 95.71,
            "AD": 85.71,
            "BD": 85.71,
        },
    }
    assert {
        case: {pair: edge["score"] for pair, edge in result["evidence"].items()}
        for case, result in cases.items()
    } == expected_scores
    assert all(
        edge["class"] == "REVIEW_SUPPORT"
        for result in cases.values()
        for edge in result["evidence"].values()
    )
    assert cases == json.loads(json.dumps(cases, sort_keys=True))
