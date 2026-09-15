"""Regression coverage for scan-independent retrieval decision ordering."""

import json

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from app.core.config import Settings
from app.core.constants import SOURCE_ROW_INDEX_FIELD
from app.db.models import IdentityDiscoveryRun, IdentityNeighborProposal, ScanRecordSnapshot
from app.services.canonical_record_service import (
    canonical_record_ref_key,
    retrieval_order_key_for_source_record,
    retrieval_pair_order_key,
)
from app.services.character_retrieval import (
    CharacterLshConfiguration,
    retrieve_lsh_directed_neighbors,
)
from app.services.hybrid_retrieval import (
    CANONICAL_RECORD_REF_FIELD,
    RETRIEVAL_ORDER_KEY_FIELD,
    HybridCandidateRetriever,
    MemoryEmbeddingVectorCache,
)
from app.services.lexical_retrieval import retrieve_exact_indexed_lexical_neighbors
from app.services.scan_runner import ScanRunner


def _rows(scan_id: int) -> pd.DataFrame:
    records = pd.DataFrame([
        {"PART_NO": "A-01", "DESCRIPTION": "precision pump assembly", "CONTRACT": "S1", "UNIT_MEAS": "EA"},
        {"PART_NO": "A-02", "DESCRIPTION": "precision pump assembly", "CONTRACT": "S1", "UNIT_MEAS": "EA"},
        {"PART_NO": "A-03", "DESCRIPTION": "precision pump assembly", "CONTRACT": "S1", "UNIT_MEAS": "EA"},
        {"PART_NO": "B-01", "DESCRIPTION": "precision pump motor", "CONTRACT": "S1", "UNIT_MEAS": "EA"},
        {"PART_NO": "B-02", "DESCRIPTION": "precision pump motor", "CONTRACT": "S1", "UNIT_MEAS": "EA"},
        {"PART_NO": "C-01", "DESCRIPTION": "hydraulic control valve", "CONTRACT": "S1", "UNIT_MEAS": "EA"},
    ])
    records[SOURCE_ROW_INDEX_FIELD] = range(len(records))
    records[CANONICAL_RECORD_REF_FIELD] = [
        canonical_record_ref_key(scan_id, index) for index in range(len(records))
    ]
    records[RETRIEVAL_ORDER_KEY_FIELD] = [
        retrieval_order_key_for_source_record(row, index)
        for index, row in enumerate(records.to_dict(orient="records"))
    ]
    return records


def _configuration() -> Settings:
    return Settings(
        llm_provider="none",
        llm_demo_enabled=False,
        hybrid_retrieval_enabled=True,
        hybrid_retrieval_lexical_top_k=1,
        hybrid_retrieval_vector_top_k=1,
        hybrid_retrieval_final_top_k=1,
        hybrid_retrieval_max_pairs_per_scan=4,
        hybrid_retrieval_tier_a_max=2,
        hybrid_retrieval_tier_b_max=1,
        hybrid_retrieval_tier_c_max=1,
        hybrid_retrieval_family_max=1,
    )


def _hybrid_semantics(result):
    return tuple(
        (
            min(item.left_record_id, item.right_record_id),
            max(item.left_record_id, item.right_record_id),
            item.retrieval_rank,
            item.retrieval_priority,
            item.retrieval_tier.value,
            item.evidence.retrieval_sources,
            item.evidence.channel_ranks,
            item.evidence.channel_scores,
        )
        for item in result.candidates
    )


def test_pair_order_key_is_endpoint_order_independent():
    assert retrieval_pair_order_key("a", "z") == retrieval_pair_order_key("z", "a")


def test_lexical_equal_score_tie_is_stable_across_scan_references():
    matrix = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5)).fit_transform(
        ["same pump", "same pump", "same pump"]
    )
    order_keys = tuple(_rows(1)[RETRIEVAL_ORDER_KEY_FIELD][:3])
    first = retrieve_exact_indexed_lexical_neighbors(matrix, order_keys, 1)
    second = retrieve_exact_indexed_lexical_neighbors(matrix, order_keys, 1)
    assert first.directed_neighbors == second.directed_neighbors


def test_character_equal_score_tie_is_stable_across_scan_references():
    matrix = np.zeros((4, 384), dtype=np.float32)
    matrix[:, 0] = 1.0
    matrix = normalize(matrix)
    order_keys = tuple(_rows(1)[RETRIEVAL_ORDER_KEY_FIELD][:4])
    configuration = CharacterLshConfiguration(
        table_count=4, bits_per_table=2, probe_radius=2, candidate_pool_k=3
    )
    first = retrieve_lsh_directed_neighbors(matrix, order_keys, 1, configuration)
    second = retrieve_lsh_directed_neighbors(matrix, order_keys, 1, configuration)
    assert first.directed_neighbors == second.directed_neighbors


def test_hybrid_ties_caps_and_cache_are_scan_independent():
    configuration = _configuration()
    first_rows = _rows(101)
    second_rows = _rows(202)
    assert tuple(first_rows[RETRIEVAL_ORDER_KEY_FIELD]) == tuple(
        second_rows[RETRIEVAL_ORDER_KEY_FIELD]
    )
    assert set(first_rows[CANONICAL_RECORD_REF_FIELD]).isdisjoint(
        set(second_rows[CANONICAL_RECORD_REF_FIELD])
    )

    cache = MemoryEmbeddingVectorCache()
    first = HybridCandidateRetriever(configuration, cache=cache).retrieve(
        first_rows, "DISCOVERY"
    )
    warm = HybridCandidateRetriever(configuration, cache=cache).retrieve(
        first_rows, "DISCOVERY"
    )
    second = HybridCandidateRetriever(
        configuration, cache=MemoryEmbeddingVectorCache()
    ).retrieve(second_rows, "DISCOVERY")

    assert _hybrid_semantics(first) == _hybrid_semantics(warm)
    assert _hybrid_semantics(first) == _hybrid_semantics(second)


def _proposal_semantics(db, scan_id: int):
    run_id = db.query(IdentityDiscoveryRun.id).filter_by(scan_id=scan_id).scalar()
    source_by_id = {
        row.id: row.source_row_index
        for row in db.query(ScanRecordSnapshot).filter_by(scan_id=scan_id)
    }
    return tuple(sorted(
        (
            *sorted((source_by_id[row.record_id_1], source_by_id[row.record_id_2])),
            row.proposal_order,
            row.proposal_priority,
            row.source_channels_json,
            row.channel_provenance_json,
            row.reciprocal_channels_json,
            json.loads(row.discovery_context_json),
        )
        for row in db.query(IdentityNeighborProposal).filter_by(discovery_run_id=run_id)
    ))


def test_three_scan_ids_persist_identical_s1_proposals_and_distinct_api_references(db):
    configuration = _configuration()
    source = _rows(1).drop(
        columns=[
            CANONICAL_RECORD_REF_FIELD,
            RETRIEVAL_ORDER_KEY_FIELD,
            SOURCE_ROW_INDEX_FIELD,
        ]
    )
    scan_ids = []
    reference_sets = []
    for index in range(3):
        scan, _result = ScanRunner(db, configuration).run(
            source.copy(), f"scan-independent-{index}", ["CONTRACT", "UNIT_MEAS"], 75
        )
        scan_ids.append(scan.id)
        reference_sets.append({
            row.record_ref_key
            for row in db.query(ScanRecordSnapshot).filter_by(scan_id=scan.id)
        })

    semantics = [_proposal_semantics(db, scan_id) for scan_id in scan_ids]
    assert semantics[0] == semantics[1] == semantics[2]
    assert all(
        reference_sets[left].isdisjoint(reference_sets[right])
        for left in range(3)
        for right in range(left + 1, 3)
    )
