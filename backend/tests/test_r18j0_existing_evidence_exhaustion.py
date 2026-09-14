import csv
from pathlib import Path

import pytest

from app.benchmarks import r18j0_existing_evidence_exhaustion as r18j0


def _observation(fingerprint="fp", label="SAME", source="R18_PAIR", pair_id="P1"):
    return {
        "canonical_pair_fingerprint": fingerprint,
        "human_label": label,
        "human_confidence": "MEDIUM",
        "human_reason": "REASON",
        "human_comment": "comment",
        "comment_basis": "",
        "review_source": source,
        "review_pair_id": pair_id,
        "evidence_precedence": 1,
    }


def _rule_row(label, **overrides):
    row = {
        "human_label": label,
        "human_confidence": "MEDIUM",
        "review_source": "R18_PAIR_REFERENCE",
        "source_visibility": "PARTIALLY_ACTIONABLE" if label == "DIFFERENT" else "NOT_APPLICABLE",
        "same_part_type": "true",
        "same_uom": "true",
        "same_site": "true",
        "technical_attribute_conflict": False,
        "model_type_conflict": False,
        "object_function_conflict": False,
        "independent_non_description_support_missing": False,
        "part_number_residual_divergence": False,
        "numeric_residual_divergence": False,
        "alphabetic_residual_divergence": False,
        "unresolved_residual_divergence": False,
        "generic_copied_description_dominance": False,
        "description_only_evidence": False,
        "identity_signature_incomplete": False,
        "provenance": "SHADOW_TRUSTED_IDENTITY_PRESENT",
        "exact_normalized_description": False,
    }
    row.update(overrides)
    return row


def _write(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_canonical_pair_fingerprint_is_order_independent_and_namespaced():
    assert r18j0.canonical_pair_fingerprint("a", "b") == r18j0.canonical_pair_fingerprint("b", "a")
    assert r18j0.canonical_pair_fingerprint("a", "b") != r18j0.canonical_pair_fingerprint("ab", "")


def test_reconciliation_deduplicates_matching_human_observations():
    rows = r18j0.reconcile_observations([
        _observation(source="R18_PAIR", pair_id="P1"),
        _observation(source="R18G_DEVELOPMENT", pair_id="G1"),
    ])
    assert len(rows) == 1
    assert rows[0]["human_label"] == "SAME"
    assert rows[0]["observation_count"] == 2
    assert rows[0]["review_pair_id"] == "G1 || P1"


def test_reconciliation_preserves_conflicting_labels_without_using_either_as_truth():
    rows = r18j0.reconcile_observations([
        _observation(label="SAME"),
        _observation(label="DIFFERENT", source="R18G_HOLDOUT", pair_id="G1"),
    ])
    assert rows[0]["human_label"] == "CONFLICTING_HUMAN_LABELS"
    assert rows[0]["human_label_observations"] == "DIFFERENT || SAME"


def test_r18_human_evidence_sources_must_reconcile(tmp_path):
    shadow, reference, mapping = (tmp_path / name for name in ("shadow.csv", "reference.csv", "mapping.csv"))
    _write(shadow, ["review_pair_id", "shadow_corrected_edge_class"], [{"review_pair_id": "P1", "shadow_corrected_edge_class": "REVIEW_SUPPORT"}])
    _write(reference, ["review_pair_id"], [{"review_pair_id": "P1"}])
    _write(mapping, ["review_pair_id"], [{"review_pair_id": "P2"}])
    with pytest.raises(r18j0.R18J0DiagnosticError, match="SOURCE_RECONCILIATION_FAILED"):
        r18j0._r18_observations(shadow, reference, mapping)


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        ({"human_label": "DIFFERENT", "comment_basis": "DOMAIN_EXTERNAL", "assessment": {}}, "EXTERNAL_KNOWLEDGE_DOMINANT"),
        ({"human_label": "DIFFERENT", "comment_basis": "", "protected_conflict": True, "assessment": {}}, "SOURCE_VISIBLE_ACTIONABLE"),
        ({"human_label": "DIFFERENT", "comment_basis": "", "part_number_residual_divergence": True, "human_comment": "visible suffix", "assessment": {}}, "PARTIALLY_ACTIONABLE"),
        ({"human_label": "DIFFERENT", "comment_basis": "", "assessment": {}}, "UNRESOLVED"),
        ({"human_label": "SAME", "comment_basis": "", "assessment": {}}, "NOT_APPLICABLE"),
    ],
)
def test_source_visibility_classification_is_deterministic(row, expected):
    assert r18j0.source_visibility_class(row) == expected


def test_candidate_rule_evaluation_accounts_for_positive_controls_deterministically():
    rows = [
        _rule_row("DIFFERENT", part_number_residual_divergence=True),
        _rule_row("SAME", part_number_residual_divergence=True),
        _rule_row("SAME"),
    ]
    first = r18j0.evaluate_rules(rows)
    second = r18j0.evaluate_rules(list(reversed(rows)))
    assert first == second
    candidate = next(row for row in first if row["candidate_rule"] == "PART_NUMBER_RESIDUAL_DIVERGENCE")
    assert candidate["human_different_strong_caught"] == 1
    assert candidate["human_same_strong_harmed"] == 1
    assert candidate["evidence_classification"] == "CONTRADICTED_BY_POSITIVE_CONTROLS"


def test_holdout_only_zero_harm_rule_is_explicitly_overfit():
    assert r18j0.classify_rule(
        different_caught=2,
        same_harmed=0,
        caught_families={"CONSUMED_HOLDOUT"},
        source_visible_caught=2,
    ) == "OVERFIT_TO_CONSUMED_HOLDOUT"


def test_demo_safe_decision_requires_no_promising_or_repeated_signal():
    classification, next_task = r18j0.demo_decision([
        {"evidence_classification": "CONTRADICTED_BY_POSITIVE_CONTROLS"},
        {"evidence_classification": "NOT_ACTIONABLE"},
    ])
    assert classification == "R18J_0_NO_SAFE_SOURCE_VISIBLE_DISCRIMINATOR"
    assert next_task == "DEMO_SAFE_PRODUCTIZATION_WITHOUT_ACCURACY_OVERCLAIM"


def test_demo_decision_routes_promising_signal_to_at_most_tiny_check_stage():
    classification, next_task = r18j0.demo_decision([
        {"evidence_classification": "PROMISING_BUT_TOO_SMALL"}
    ])
    assert classification == "R18J_0_PROMISING_SIGNAL_REQUIRES_TINY_HUMAN_CHECK"
    assert next_task == "R18J_1_TINY_TARGETED_HUMAN_CHECK"


def test_analysis_module_has_no_runtime_mutation_or_provider_path():
    source = Path(r18j0.__file__).read_text(encoding="utf-8")
    for token in ("INSERT INTO", "UPDATE ", "DELETE FROM", "DROP TABLE", "ALTER TABLE"):
        assert token not in source
    assert "app.llm" not in source
    assert "provider_calls\": 0" in source
    assert r18j0.DEMO_CONTRACT == "ADVISORY_REQUIRES_HUMAN_REVIEW"
