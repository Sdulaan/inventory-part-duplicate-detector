"""Determinism regressions for cache representation and GF5 traversal."""

import numpy as np
import pandas as pd

from app.core.config import Settings
from app.core.constants import SOURCE_ROW_INDEX_FIELD
from app.engine.identity_edge import IdentityEdgeClass
from app.resolution.contracts import (
    IdentityResolutionEvidenceEdge,
    IdentityResolutionInput,
    IdentityResolutionNeighborhood,
    ResolverConfiguration,
)
from app.resolution.resolver import resolve_identity_groups
from app.services.canonical_record_service import (
    CanonicalScanRecord,
    canonical_record_ref_key,
    retrieval_order_key_for_source_record,
)
from app.services.hybrid_retrieval import (
    CANONICAL_RECORD_REF_FIELD,
    RETRIEVAL_ORDER_KEY_FIELD,
    HybridCandidateRetriever,
    SqlAlchemyEmbeddingVectorCache,
    canonical_embedding_vector,
)


def _configuration() -> Settings:
    return Settings(
        llm_provider="none",
        llm_demo_enabled=False,
        hybrid_retrieval_enabled=True,
        hybrid_retrieval_lexical_top_k=2,
        hybrid_retrieval_vector_top_k=2,
        hybrid_retrieval_final_top_k=2,
        hybrid_retrieval_max_pairs_per_scan=12,
    )


def _retrieval_rows(scan_id: int) -> pd.DataFrame:
    frame = pd.DataFrame([
        {"PART_NO": "P-1", "DESCRIPTION": "MOTOR BEARING 6205", "CONTRACT": "S1", "UNIT_MEAS": "EA"},
        {"PART_NO": "P-2", "DESCRIPTION": "MOTOR BEARING 6206", "CONTRACT": "S1", "UNIT_MEAS": "EA"},
        {"PART_NO": "P-3", "DESCRIPTION": "MOTOR BEARING 6207", "CONTRACT": "S1", "UNIT_MEAS": "EA"},
        {"PART_NO": "P-4", "DESCRIPTION": "MOTOR BEARING 6208", "CONTRACT": "S1", "UNIT_MEAS": "EA"},
    ])
    frame[SOURCE_ROW_INDEX_FIELD] = range(len(frame))
    frame[CANONICAL_RECORD_REF_FIELD] = [
        canonical_record_ref_key(scan_id, index) for index in range(len(frame))
    ]
    frame[RETRIEVAL_ORDER_KEY_FIELD] = [
        retrieval_order_key_for_source_record(row, index)
        for index, row in enumerate(frame.to_dict(orient="records"))
    ]
    return frame


def _candidate_semantics(result):
    return tuple(
        (
            item.left_record_id,
            item.right_record_id,
            item.retrieval_rank,
            item.retrieval_priority,
            item.evidence.channel_ranks,
            item.evidence.channel_scores,
        )
        for item in result.candidates
    )


def test_cache_miss_and_repeated_hits_use_exact_same_vector_and_candidates(db):
    raw = np.asarray([0.20412415266036987] + [0.0] * 383, dtype=np.float32)
    expected = canonical_embedding_vector(raw)
    cache = SqlAlchemyEmbeddingVectorCache(db)
    cache.save({"vector": raw}, "model")
    assert np.array_equal(cache.load(["vector"], "model")["vector"], expected)

    rows = _retrieval_rows(101)
    first = HybridCandidateRetriever(_configuration(), cache=cache).retrieve(
        rows, "DISCOVERY"
    )
    second = HybridCandidateRetriever(_configuration(), cache=cache).retrieve(
        rows, "DISCOVERY"
    )
    third = HybridCandidateRetriever(_configuration(), cache=cache).retrieve(
        rows, "DISCOVERY"
    )
    assert _candidate_semantics(first) == _candidate_semantics(second)
    assert _candidate_semantics(second) == _candidate_semantics(third)


def _record(record_id: int, scan_id: int, ordinal: int) -> CanonicalScanRecord:
    return CanonicalScanRecord(
        record_id=record_id,
        scan_id=scan_id,
        source_row_index=ordinal,
        record_ref_key=f"scan-{scan_id}-row-{ordinal}",
        source_record_fingerprint=f"semantic-source-{ordinal}",
        part_no=f"P-{ordinal}",
        description=f"SPECIFIC ITEM {ordinal}",
        contract="S1",
        uom="EA",
        type_code=None,
        prime_commodity=None,
        second_commodity=None,
        accounting_group=None,
        part_product_code=None,
        part_product_family=None,
        product_category_id=None,
        hsn_sac_code=None,
        hazard_code=None,
        normalized_part_no=f"P{ordinal}",
        normalized_description=f"SPECIFIC ITEM {ordinal}",
        normalization_version="test-v1",
    )


def _resolution_input(scan_id: int, ids_by_ordinal: tuple[int, ...]):
    records = tuple(
        _record(record_id, scan_id, ordinal)
        for ordinal, record_id in enumerate(ids_by_ordinal)
    )
    classes = {}
    for left in range(5):
        for right in range(left + 1, 5):
            if {left, right} == {3, 4} or {left, right} <= {0, 1, 2}:
                classes[(left, right)] = (
                    IdentityEdgeClass.REVIEW_SUPPORT
                    if {left, right} == {1, 2}
                    else IdentityEdgeClass.STRONG_SUPPORT
                )
            else:
                classes[(left, right)] = IdentityEdgeClass.NON_GROUPABLE
    edges = []
    for (left, right), edge_class in classes.items():
        first, second = sorted((ids_by_ordinal[left], ids_by_ordinal[right]))
        edges.append(IdentityResolutionEvidenceEdge(
            scan_id=scan_id,
            evidence_run_id=scan_id * 10,
            record_id_1=first,
            record_id_2=second,
            edge_class=edge_class,
            reason_codes=(f"TEST_{edge_class.value}",),
            evidence_fingerprint=f"scan-{scan_id}-edge-{left}-{right}",
        ))
    return IdentityResolutionInput(
        scan_id=scan_id,
        discovery_run_id=scan_id * 10 - 1,
        evidence_run_id=scan_id * 10,
        canonical_records=records,
        identity_neighborhoods=(IdentityResolutionNeighborhood(
            f"scan-{scan_id}-neighborhood",
            scan_id,
            scan_id * 10 - 1,
            tuple(sorted(ids_by_ordinal)),
            False,
            False,
        ),),
        machine_evidence_edges=tuple(edges),
        human_constraints=(),
        resolver_algorithm_version="constrained-identity-resolver-v1",
        resolver_configuration=ResolverConfiguration(20, 40, 8, "resolver-config-v1"),
    )


def _resolution_semantics(value, result):
    ordinal_by_id = {
        record.record_id: record.source_row_index for record in value.canonical_records
    }
    return tuple(sorted(
        (
            tuple(sorted(ordinal_by_id[item] for item in group.member_record_ids)),
            group.status.value,
        )
        for group in result.accepted_groups
    ))


def test_gf5_partition_traversal_is_independent_of_database_id_assignment():
    first_input = _resolution_input(101, (1, 2, 3, 4, 5))
    second_input = _resolution_input(202, (105, 101, 104, 102, 103))
    first = resolve_identity_groups(first_input, None)
    second = resolve_identity_groups(second_input, None)
    assert _resolution_semantics(first_input, first) == _resolution_semantics(
        second_input, second
    )
    assert first.metrics.candidate_partitions_explored == (
        second.metrics.candidate_partitions_explored
    )
    assert first.metrics.accepted_group_count == second.metrics.accepted_group_count
