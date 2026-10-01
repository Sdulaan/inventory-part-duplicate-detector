from types import SimpleNamespace

import pandas as pd

from app.engine import candidate_generator
from app.engine.candidate_generator import generate_candidate_pairs
from app.resolution import resolver
from app.services.hybrid_retrieval import scaled_hybrid_caps


def _caps(**overrides):
    values = dict(
        hybrid_retrieval_max_pairs_per_scan=500,
        hybrid_retrieval_tier_a_max=250,
        hybrid_retrieval_tier_b_max=200,
        hybrid_retrieval_tier_c_max=50,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def test_hybrid_caps_grow_with_the_file():
    total, tiers = scaled_hybrid_caps(_caps(hybrid_retrieval_pairs_per_record=3), 100_000)
    assert total == 300_000
    assert tiers == {"TIER_A": 150_000, "TIER_B": 120_000, "TIER_C": 30_000}


def test_configured_caps_are_a_floor_and_scaling_can_be_disabled():
    assert scaled_hybrid_caps(_caps(hybrid_retrieval_pairs_per_record=3), 100)[0] == 500
    assert scaled_hybrid_caps(_caps(hybrid_retrieval_pairs_per_record=0), 100_000)[0] == 500
    assert scaled_hybrid_caps(_caps(), 100_000) == (
        500, {"TIER_A": 250, "TIER_B": 200, "TIER_C": 50}
    )


def _parts(site_sizes):
    rows = []
    for site, size in site_sizes.items():
        rows += [
            {"PART_NO": f"{site}-{index}", "DESCRIPTION": f"Part {index}", "CONTRACT": site}
            for index in range(size)
        ]
    return pd.DataFrame(rows)


def test_blocks_are_compared_completely_or_left_to_similarity(monkeypatch):
    monkeypatch.setattr(candidate_generator, "MAX_CANDIDATE_PAIRS", 20)
    # S1 needs 45 pairs (over the limit); S2 needs 6 and S3 needs 10.
    pairs = generate_candidate_pairs(_parts({"S1": 10, "S2": 4, "S3": 5}), ["CONTRACT"])

    sites = {pair["record_a"]["CONTRACT"] for pair in pairs}
    assert sites == {"S2", "S3"}
    assert len(pairs) == 6 + 10
    assert pairs[0]["warnings"][-1]["warning_type"] == "PAIR_LIMIT_REACHED"


def test_blocks_within_the_limit_keep_every_pair():
    pairs = generate_candidate_pairs(_parts({"S1": 6}), ["CONTRACT"])
    assert len(pairs) == 15
    assert not any(pair["warnings"] for pair in pairs)


def test_partition_search_handles_more_candidates_than_the_recursion_limit():
    value = SimpleNamespace(resolver_configuration=SimpleNamespace(
        max_resolution_members=20, max_targeted_checks_per_work_unit=40,
    ))
    candidates = [
        resolver._Candidate(
            SimpleNamespace(
                status=None, member_record_ids=(index,), hypothesis_fingerprint=str(index),
                evidence_summary=SimpleNamespace(strong_support_count=0, review_support_count=0),
            ),
            frozenset({index}), (1, 0, 0), (f"key-{index:05d}",),
        )
        for index in range(2_000)
    ]
    counters = resolver._ExecutionCounters()
    selected, exhausted, ambiguous = resolver._select_partition(value, candidates, counters)
    # 2,000 candidates exceed the search budget; the search must stop cleanly.
    assert exhausted is True
    assert selected == ()
