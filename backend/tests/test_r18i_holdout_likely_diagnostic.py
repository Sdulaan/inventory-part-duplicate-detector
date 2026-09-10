from pathlib import Path

import pytest

from app.benchmarks import r18i_holdout_likely_diagnostic as r18i


def _row(index: int, label: str, basis: str = "UNCLEAR") -> dict[str, str]:
    return {
        "review_group_id": f"R18G-{index:02d}",
        "system_status": r18i.LIKELY,
        "normalized_group_label": label,
        "comment_basis": basis,
    }


def _pair(*, provenance="SHADOW_LEXICAL_ONLY_OR_UNRESOLVED", conflicts=(), unresolved=3):
    return {
        "edge_class": r18i.STRONG,
        "support_provenance": provenance,
        "protected_conflicts": list(conflicts),
        "unresolved_discriminator_count": unresolved,
    }


def test_select_likely_cases_requires_exact_six_failures_and_two_controls():
    rows = [_row(i, r18i.NOT_ONE) for i in range(6)]
    rows += [_row(i + 6, r18i.SAME) for i in range(2)]
    rows.append({**_row(99, r18i.NOT_ONE), "system_status": "REVIEW_GROUP"})

    failures, controls = r18i.select_likely_cases(reversed(rows))

    assert [row["review_group_id"] for row in failures] == [f"R18G-{i:02d}" for i in range(6)]
    assert [row["review_group_id"] for row in controls] == ["R18G-06", "R18G-07"]


def test_select_likely_cases_fails_closed_on_an_incomplete_case_set():
    with pytest.raises(r18i.R18IDiagnosticError, match="EXACT_LIKELY_CASE_SET_INVALID"):
        r18i.select_likely_cases([_row(i, r18i.NOT_ONE) for i in range(5)])


@pytest.mark.parametrize(
    ("classes", "expected"),
    [
        ([r18i.STRONG], "ALL_STRONG"),
        ([r18i.STRONG, r18i.REVIEW], "STRONG_CORE_WITH_REVIEW_BRIDGE"),
        ([r18i.REVIEW], "REVIEW_DOMINATED"),
        ([r18i.STRONG, "CANNOT_LINK"], "MIXED_EVIDENCE"),
    ],
)
def test_pair_topology_reconstruction(classes, expected):
    assert r18i.topology_class(classes) == expected


def test_likely_promotion_requires_complete_all_strong_pairwise_evidence():
    trace = r18i.likely_promotion_trace([r18i.STRONG])
    assert trace == {
        "promoted": True,
        "rule": "ALL_INTERNAL_PAIRS_STRONG_COMPLETE_PAIRWISE",
        "all_pairs_strong": True,
        "complete_pairwise": True,
        "unresolved_bridge": False,
    }
    assert not r18i.likely_promotion_trace([r18i.STRONG, r18i.REVIEW])["promoted"]
    assert not r18i.likely_promotion_trace([r18i.STRONG], complete=False)["promoted"]


def test_membership_status_diagnosis_separates_external_and_lexical_cases():
    assert r18i.membership_status_diagnosis(
        _row(1, r18i.NOT_ONE, "DOMAIN_EXTERNAL"), _pair()
    ) == "DATA_INSUFFICIENCY_OR_EXTERNAL_KNOWLEDGE"
    assert r18i.membership_status_diagnosis(
        _row(2, r18i.NOT_ONE), _pair()
    ) == "STATUS_PROMOTION_ERROR"
    assert r18i.membership_status_diagnosis(
        _row(3, r18i.NOT_ONE), _pair(conflicts=("SIDE_CONFLICT",))
    ) == "MIXED_CAUSE"


def test_external_domain_actionability_is_bounded_by_visible_evidence():
    row = _row(1, r18i.NOT_ONE, "DOMAIN_EXTERNAL")
    assert r18i.actionability(row, _pair(unresolved=0)) == "NOT_ACTIONABLE_FROM_AVAILABLE_INPUT"
    assert r18i.actionability(row, _pair(unresolved=2)) == "PARTIALLY_ACTIONABLE"
    assert r18i.actionability(row, _pair(conflicts=("SIDE_CONFLICT",))) == "DETERMINISTICALLY_ACTIONABLE"
    assert r18i.actionability(_row(2, r18i.NOT_ONE), _pair()) == "MIXED_OR_UNCLEAR"


def test_gf5_objective_is_not_primary_for_the_only_two_member_candidate():
    assert r18i.gf5_objective_causality(member_count=2, eligible_group_count=1) == "GF5_NOT_PRIMARY_CAUSE"
    assert r18i.gf5_objective_causality(member_count=3, eligible_group_count=2) == "UNKNOWN"


def test_shadow_policies_only_retain_or_downgrade_current_likely_status():
    lexical = {
        "possible_pair_count": 1,
        "strong_edge_count": 1,
        "review_edge_count": 0,
        "support_provenance": "SHADOW_LEXICAL_ONLY_OR_UNRESOLVED",
    }
    trusted = {**lexical, "support_provenance": "SHADOW_TRUSTED_IDENTITY_PRESENT"}
    assert r18i.shadow_policy(lexical) == {
        "S1_ALL_INTERNAL_PAIRS_STRONG": True,
        "S2_MINIMUM_STRONG_DENSITY": True,
        "S3_ANY_REVIEW_REMAINS_REVIEW": True,
        "S4_WEAKEST_LINK_STRONG": True,
        "S5_TRUSTED_PATH_PER_MEMBER": False,
    }
    assert all(r18i.shadow_policy(trusted).values())
    assert not any(r18i.shadow_policy({**lexical, "strong_edge_count": 0, "review_edge_count": 1}).values())


def test_diagnostic_is_read_only_and_freezes_the_decision_contract():
    source = Path(r18i.__file__).read_text(encoding="utf-8")
    assert "?mode=ro" in source
    for mutating_sql in ("INSERT INTO", "UPDATE ", "DELETE FROM", "DROP TABLE", "ALTER TABLE"):
        assert mutating_sql not in source
    assert r18i.CLASSIFICATION == "R18I_NO_SAFE_GENERAL_CAUSE_PROVEN"
    assert r18i.NEXT == "NEW_HUMAN_EVIDENCE_FOR_UNRESOLVED_CAUSE"
    assert r18i.HOLDOUT_STATUS == "CONSUMED_FOR_DIAGNOSTIC_USE"
    assert r18i.POST_CORRECTION_HOLDOUT_REQUIRED == "YES"
