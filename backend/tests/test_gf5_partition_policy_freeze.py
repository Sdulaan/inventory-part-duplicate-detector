"""Regression freeze for the unchanged GF5 partition-selection policy."""

from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

from app.resolution import resolver
from app.resolution.contracts import (
    IdentityGroupHypothesisStatus,
    ResolverConfiguration,
)
from app.resolution.fingerprints import fingerprint_payload


POLICY_ID = "GF5_PARTITION_POLICY_V1"
OBJECTIVE = ("covered", "likely_members", "strong", "-review", "-group_count")
CONFIGURATION_FINGERPRINT = (
    "2584f95836d0f37d73dea545d64eab6b9cfbefc67cfa29d5dd0a01b5fda92448"
)
POLICY_FINGERPRINT = (
    "0a073ca6b0b06e31f115e892a8a27b579717cdf483f6923cc8f7bc6d362d2826"
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _candidate(
    fingerprint: str,
    members: tuple[int, ...],
    *,
    likely: bool = False,
    strong: int = 0,
    review: int = 0,
):
    status = (
        IdentityGroupHypothesisStatus.LIKELY_DUPLICATE_GROUP
        if likely
        else IdentityGroupHypothesisStatus.POSSIBLE_DUPLICATE_GROUP_REVIEW
    )
    group = SimpleNamespace(
        hypothesis_id=fingerprint,
        hypothesis_fingerprint=fingerprint,
        member_record_ids=members,
        status=status,
        evidence_summary=SimpleNamespace(
            strong_support_count=strong,
            review_support_count=review,
        ),
    )
    return resolver._Candidate(group, frozenset(members), (0, 0, 0))


def _select(*candidates):
    value = SimpleNamespace(
        resolver_configuration=ResolverConfiguration(
            max_resolution_members=20,
            max_targeted_checks_per_work_unit=40,
            complete_pairwise_member_limit=8,
            configuration_version="constrained-identity-resolver-config-v1",
        )
    )
    return resolver._select_partition(
        value,
        candidates,
        resolver._ExecutionCounters(),
    )


def _selected_ids(*candidates) -> tuple[str, ...]:
    selected, exhausted, ambiguous = _select(*candidates)
    assert exhausted is False
    assert ambiguous is False
    return tuple(group.hypothesis_id for group in selected)


def test_runtime_objective_source_is_frozen_in_exact_order():
    source = inspect.getsource(resolver._select_partition)
    assert "objective = (covered, likely_members, strong, -review, -len(groups))" in source


def test_coverage_is_the_first_objective_component():
    larger_review = _candidate("larger-review", (1, 2, 3), review=2)
    smaller_likely = _candidate("smaller-likely", (1, 2), likely=True, strong=1)
    assert _selected_ids(larger_review, smaller_likely) == ("larger-review",)


def test_likely_members_are_the_second_objective_component():
    likely = _candidate("likely", (1, 2), likely=True, strong=1, review=1)
    review = _candidate("review", (1, 2), strong=1, review=1)
    assert _selected_ids(likely, review) == ("likely",)


def test_strong_support_is_the_third_objective_component():
    stronger = _candidate("stronger", (1, 2), strong=2, review=1)
    weaker = _candidate("weaker", (1, 2), strong=1, review=1)
    assert _selected_ids(stronger, weaker) == ("stronger",)


def test_fewer_review_contributions_are_the_fourth_objective_component():
    lower_review = _candidate("lower-review", (1, 2), strong=1, review=1)
    higher_review = _candidate("higher-review", (1, 2), strong=1, review=2)
    assert _selected_ids(lower_review, higher_review) == ("lower-review",)


def test_fewer_groups_are_the_fifth_objective_component():
    one_group = _candidate("one-group", (1, 2, 3, 4), strong=2, review=2)
    left = _candidate("left", (1, 2), strong=1, review=1)
    right = _candidate("right", (3, 4), strong=1, review=1)
    assert _selected_ids(one_group, left, right) == ("one-group",)


def test_equal_best_partitions_emit_only_the_stable_intersection_and_defer():
    left = _candidate("left", (1, 2), strong=1, review=1)
    right = _candidate("right", (2, 3), strong=1, review=1)
    selected, exhausted, ambiguous = _select(left, right)
    assert selected == ()
    assert exhausted is False
    assert ambiguous is True


def test_development_case_one_structurally_prefers_the_exact_partition():
    first = _candidate("current-a", (1, 2, 3), strong=2, review=0)
    second = _candidate("current-b", (4, 5), strong=1, review=0)
    coarse = _candidate("adr-coarse", (1, 2, 3, 4, 5), strong=3, review=6)
    assert _selected_ids(first, second, coarse) == ("current-a", "current-b")


def test_development_case_two_structurally_prefers_less_false_coarsening():
    first = _candidate("current-a", (1, 2), strong=1, review=1)
    second = _candidate("current-b", (3, 4), strong=1, review=1)
    coarse = _candidate("adr-coarse", (1, 2, 3, 4), strong=2, review=6)
    assert _selected_ids(first, second, coarse) == ("current-a", "current-b")


def test_frozen_configuration_and_policy_identifiers_are_documented():
    configuration = ResolverConfiguration(
        max_resolution_members=20,
        max_targeted_checks_per_work_unit=40,
        complete_pairwise_member_limit=8,
        configuration_version="constrained-identity-resolver-config-v1",
    )
    assert (
        fingerprint_payload("resolver-configuration", configuration)
        == CONFIGURATION_FINGERPRINT
    )

    policy = (REPOSITORY_ROOT / "docs" / "GF5_PARTITION_POLICY.md").read_text(
        encoding="utf-8"
    )
    assert f"policy_id: {POLICY_ID}" in policy
    assert "objective: (" + ", ".join(OBJECTIVE) + ")" in policy
    assert POLICY_FINGERPRINT in policy
    assert "GF5-GROUP-PARTITION-RESIDUAL-MIXING` is `OPEN" in policy


def test_architecture_document_matches_the_frozen_runtime_policy():
    adr = (
        REPOSITORY_ROOT / "docs" / "GROUP_FIRST_IDENTITY_ARCHITECTURE_ADR.md"
    ).read_text(encoding="utf-8")
    assert POLICY_ID in adr
    assert "(covered, likely_members, strong, -review, -group_count)" in adr
    assert "then review support" not in adr
    assert "stable-intersection/defer behavior" in adr
