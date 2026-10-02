"""Regression tests for deferred families of identical or fully supported records.

* Partition-search pruning returns exactly what the exhaustive search returns.
* Fully supported families of 7 and 8 records resolve instead of exhausting
  the partition-search budget.
* Records with one identical description and only (generic) review support
  form one REVIEW group instead of being deferred as tied splits.
* Generic chaining through different text and neutral gaps still defer.
"""

import json
import random
from itertools import combinations
from types import SimpleNamespace

from app.engine.identity_edge import IdentityEdgeClass
from app.engine.identity_evidence_evaluator import (
    evaluate_canonical_identity_relationship,
    generic_only_from_evidence,
)
from app.resolution import resolver
from app.resolution.contracts import (
    DeferredIdentityReason,
    IdentityGroupHypothesisStatus,
    ResolverConfiguration,
)
from app.resolution.resolver import resolve_identity_groups
from tests.test_identity_resolver import (
    FakeTargetedProvider,
    edge,
    memberships,
    record,
    resolver_input,
    statuses,
)
from tests.test_identity_support_corrections import CONTEXT, canonical


STRONG = IdentityEdgeClass.STRONG_SUPPORT
REVIEW = IdentityEdgeClass.REVIEW_SUPPORT
REVIEW_STATUS = IdentityGroupHypothesisStatus.POSSIBLE_DUPLICATE_GROUP_REVIEW


def _resolve(descriptions, edge_class=REVIEW, *, generic=True, overrides=None):
    count = len(descriptions)
    records = [
        record(index + 1, description=description)
        for index, description in enumerate(descriptions)
    ]
    edges = [
        edge(left, right, (overrides or {}).get((left, right), edge_class), generic=generic)
        for left, right in combinations(range(1, count + 1), 2)
    ]
    return resolve_identity_groups(
        resolver_input(records, edges), FakeTargetedProvider()
    )


def _deferred(result):
    return tuple((item.record_ids, item.reason) for item in result.deferred_work_units)


def test_single_word_identical_descriptions_are_generic_review_support():
    evaluated = evaluate_canonical_identity_relationship(
        canonical(1, "218274", "Magnolia"), canonical(2, "327601", "MAGNOLIA"), CONTEXT,
    )
    assert evaluated.edge_class == REVIEW
    assert generic_only_from_evidence(json.loads(evaluated.generic_evidence_json))


def test_three_identical_generic_records_form_one_review_group():
    result = _resolve(["Magnolia", "MAGNOLIA", "Magnolia"])
    assert memberships(result) == ((1, 2, 3),)
    assert statuses(result) == (REVIEW_STATUS,)
    assert _deferred(result) == ()


def test_larger_identical_generic_families_form_one_review_group():
    for count in range(4, 9):
        result = _resolve(["Chamaerops humilis"] * count)
        assert memberships(result) == (tuple(range(1, count + 1)),), count
        assert statuses(result) == (REVIEW_STATUS,)
        assert _deferred(result) == ()


def test_identical_non_generic_review_family_forms_one_review_group():
    result = _resolve(["Rosa The Fairy"] * 4, generic=False)
    assert memberships(result) == ((1, 2, 3, 4),)
    assert statuses(result) == (REVIEW_STATUS,)


def test_generic_chaining_through_different_text_still_defers():
    result = _resolve(["BOLT", "BOLT M6", "BOLT"])
    assert memberships(result) == ()
    assert _deferred(result) == (
        ((1, 2, 3), DeferredIdentityReason.UNRESOLVED_OWNERSHIP_AMBIGUITY),
    )


def test_identical_generic_records_with_a_neutral_gap_still_defer():
    result = _resolve(
        ["Magnolia"] * 3, overrides={(1, 3): IdentityEdgeClass.NON_GROUPABLE},
    )
    assert memberships(result) == ()
    assert _deferred(result) == (
        ((1, 2, 3), DeferredIdentityReason.UNRESOLVED_OWNERSHIP_AMBIGUITY),
    )


def test_identical_set_does_not_absorb_a_record_with_different_text():
    result = _resolve(["Magnolia"] * 4 + ["Magnolia kobus"])
    assert memberships(result) == ((1, 2, 3, 4),)


def test_fully_strong_families_of_seven_and_eight_resolve():
    for count in (7, 8):
        result = _resolve(
            [f"SPECIFIC ITEM MODEL {index}" for index in range(count)],
            STRONG, generic=False,
        )
        assert memberships(result) == (tuple(range(1, count + 1)),), count
        assert statuses(result) == (IdentityGroupHypothesisStatus.LIKELY_DUPLICATE_GROUP,)
        assert _deferred(result) == ()


def _value():
    return SimpleNamespace(resolver_configuration=ResolverConfiguration(
        max_resolution_members=20,
        max_targeted_checks_per_work_unit=40,
        complete_pairwise_member_limit=8,
        configuration_version="constrained-identity-resolver-config-v1",
    ))


def _candidate(key, members, likely, strong, review):
    status = (
        IdentityGroupHypothesisStatus.LIKELY_DUPLICATE_GROUP if likely else REVIEW_STATUS
    )
    group = SimpleNamespace(
        hypothesis_id=key, hypothesis_fingerprint=key,
        member_record_ids=tuple(sorted(members)), status=status,
        evidence_summary=SimpleNamespace(
            strong_support_count=strong, review_support_count=review,
        ),
    )
    return resolver._Candidate(group, frozenset(members), (0, 0, 0), (key,))


def _exhaustive(candidates):
    best, partitions = None, set()
    for size in range(len(candidates) + 1):
        for chosen in combinations(range(len(candidates)), size):
            members = [candidates[item].members for item in chosen]
            if sum(map(len, members)) != len(frozenset().union(*members)):
                continue
            groups = [candidates[item].group for item in chosen]
            objective = (
                sum(map(len, members)),
                sum(len(group.member_record_ids) for group in groups
                    if group.status == IdentityGroupHypothesisStatus.LIKELY_DUPLICATE_GROUP),
                sum(group.evidence_summary.strong_support_count for group in groups),
                -sum(group.evidence_summary.review_support_count for group in groups),
                -len(groups),
            )
            signature = tuple(sorted(candidates[item].semantic_member_key for item in chosen))
            if best is None or objective > best:
                best, partitions = objective, {signature}
            elif objective == best:
                partitions.add(signature)
    return partitions


def test_pruned_partition_search_matches_exhaustive_search():
    generator = random.Random(20261002)
    for _ in range(400):
        members = list(range(1, generator.randint(3, 7) + 1))
        candidates = []
        for index in range(generator.randint(1, 12)):
            chosen = generator.sample(members, generator.randint(2, len(members)))
            pairs = len(chosen) * (len(chosen) - 1) // 2
            strong = generator.randint(0, pairs)
            candidates.append(_candidate(
                f"c{index:02d}", chosen, generator.random() < 0.3,
                strong, generator.randint(0, pairs - strong),
            ))
        expected = _exhaustive(candidates)
        selected, exhausted, ambiguous = resolver._select_partition(
            _value(), candidates, resolver._ExecutionCounters()
        )
        assert exhausted is False
        assert ambiguous is (len(expected) > 1)
        common = set.intersection(*(set(item) for item in expected))
        assert tuple(group.hypothesis_id for group in selected) == tuple(
            key for (key,) in sorted(common)
        )
