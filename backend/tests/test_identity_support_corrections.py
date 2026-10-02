"""Regression tests for the identity-support corrections.

Each test pins one invariant:
* a DOWNGRADE rule lowers status and never raises it;
* agreement that does not identify an item stays REVIEW_SUPPORT, even at 100;
* role wording agrees as context, not trusted identity;
* fuzzy part-number similarity is not identity evidence, the same reference
  written differently is;
* strict condition fields scope one scan instead of creating CANNOT_LINK;
* ambiguous ownership defers only the records it leaves unresolved.
"""

import json

from app.engine.business_rules import condition_values_differ
from app.engine.identity_edge import IdentityEdgeClass
from app.engine.identity_evidence_evaluator import (
    DeterministicIdentityContext,
    evaluate_canonical_identity_relationship,
    generic_only_from_evidence,
)
from app.engine.identity_signature_derivation import derive_identity_signature
from app.engine.identity_support_sufficiency import LOW_INFORMATION_REVIEW_REASON
from app.engine.normalizer import normalize_description
from app.engine.scoring import score_candidate
from app.engine.signed_identity_evidence import (
    ShadowEvidenceBucket,
    classify_shadow_evidence,
    derive_signed_identity_evidence,
)
from app.resolution.request_constraints import (
    field_group_constraint,
    group_satisfies_request_constraints,
)
from app.resolution.resolver import resolve_identity_groups
from app.services.canonical_record_service import CanonicalScanRecord
from tests.test_identity_resolver import (
    FakeTargetedProvider,
    edge,
    memberships,
    record,
    resolver_input,
)


CONTEXT = DeterministicIdentityContext("SAME_SITE_DUPLICATE", ())


def canonical(record_id, part_no, description, **extra):
    return CanonicalScanRecord(
        record_id, 1, record_id - 1, f"ref-{record_id}", f"fp-{record_id}",
        part_no, description, "S1", "PCS", None, None, None, None, None, None,
        None, None, None, part_no.casefold(), normalize_description(description),
        "test-v1", extra_fields=tuple(sorted(extra.items())),
    )


def evaluate(
    description_left, description_right, part_left="A-1", part_right="ZZ-77",
    context=CONTEXT, left=None, right=None,
):
    return evaluate_canonical_identity_relationship(
        canonical(1, part_left, description_left, **(left or {})),
        canonical(2, part_right, description_right, **(right or {})),
        context,
    )


def test_context_mismatch_never_turns_an_unrelated_pair_into_review_support():
    result = score_candidate(
        {"PART_NO": "A", "DESCRIPTION": "HVAC FAN MOTOR"},
        {"PART_NO": "B", "DESCRIPTION": "VEHICLE WIPER BLADE"},
        [],
    )
    assert result["rejection_reason"] == "APPLICATION_CONTEXT_MISMATCH"
    assert result["final_score"] < 60
    assert result["business_status"] == "INSUFFICIENT_DATA"
    assert evaluate("HVAC FAN MOTOR", "VEHICLE WIPER BLADE").edge_class == (
        IdentityEdgeClass.NON_GROUPABLE
    )


def test_rule_downgrades_never_raise_business_status_above_the_score_band():
    for left, right in (
        ("HVAC FAN MOTOR", "VEHICLE WIPER BLADE"),
        ("HVAC PIPE 20X30", "VEHICLE PIPE 30X20"),
        ("PIPE 20X30 GALV", "PIPE 30X20 GALV"),
    ):
        result = score_candidate(
            {"PART_NO": "A", "DESCRIPTION": left},
            {"PART_NO": "B", "DESCRIPTION": right},
            [],
        )
        if result["final_score"] < 60:
            assert result["business_status"] == "INSUFFICIENT_DATA"


def test_category_only_agreement_scores_100_but_stays_review_support():
    for description in ("INDUSTRIAL COMPONENT", "MAIN ASSEMBLY", "STANDARD COMPONENT"):
        relationship = evaluate(description, description)
        assert relationship.deterministic_score == 100.0
        assert relationship.edge_class == IdentityEdgeClass.REVIEW_SUPPORT
        assert LOW_INFORMATION_REVIEW_REASON in relationship.classification_reason_codes
        generic = json.loads(relationship.generic_evidence_json)
        assert generic["low_information_identity"] is True
        assert generic_only_from_evidence(generic) is True


def test_identifying_numbers_and_informative_wording_keep_strong_support():
    for description in (
        "BEARING 6205 2RS", "CONTACTOR 3P 25A 230V",
        "AIR FILTER ELEMENT", "HYDRAULIC PUMP SEAL",
    ):
        relationship = evaluate(description, description)
        assert relationship.edge_class == IdentityEdgeClass.STRONG_SUPPORT, description
        assert generic_only_from_evidence(
            json.loads(relationship.generic_evidence_json)
        ) is False


def test_category_level_fields_do_not_corroborate_but_specific_fields_do():
    category = DeterministicIdentityContext(
        "SAME_SITE_DUPLICATE", ("ACCOUNTING_GROUP", "HSN_SAC_CODE")
    )
    same_category = evaluate(
        "INDUSTRIAL COMPONENT", "INDUSTRIAL COMPONENT", context=category,
    )
    assert same_category.edge_class == IdentityEdgeClass.REVIEW_SUPPORT

    specific = DeterministicIdentityContext("SAME_SITE_DUPLICATE", ("MANUFACTURER_PART",))
    same_manufacturer_part = evaluate(
        "INDUSTRIAL COMPONENT", "INDUSTRIAL COMPONENT", context=specific,
        left={"MANUFACTURER_PART": "XK-991"}, right={"MANUFACTURER_PART": "XK-991"},
    )
    assert same_manufacturer_part.edge_class == IdentityEdgeClass.STRONG_SUPPORT


def test_role_agreement_is_context_not_trusted_identity_support():
    def signature(reference):
        return derive_identity_signature(
            {"PART_NO": reference, "DESCRIPTION": "INDUSTRIAL COMPONENT"},
            record_reference=reference,
        )

    evidence = derive_signed_identity_evidence(signature("r1"), signature("r2"))
    assert classify_shadow_evidence(evidence) != (
        ShadowEvidenceBucket.SHADOW_TRUSTED_IDENTITY_PRESENT
    )
    assert "SHADOW_ROLE_AGREEMENT_NOT_IDENTITY" in {
        fact.reason_code for fact in evidence.facts
    }


def test_fuzzy_part_number_similarity_does_not_rescue_a_generic_description():
    near = evaluate("BEARING", "BEARING", part_left="PUMP-10001", part_right="PUMP-10002")
    assert near.edge_class == IdentityEdgeClass.REVIEW_SUPPORT
    assert near.rejection_reason == "GENERIC_DESCRIPTION"

    same_reference = evaluate(
        "BEARING", "BEARING", part_left="BRG-6205-A", part_right="BRG6205A",
    )
    assert same_reference.edge_class == IdentityEdgeClass.STRONG_SUPPORT


def test_strict_condition_field_is_scan_scope_not_cannot_link():
    strict = DeterministicIdentityContext(
        "SAME_SITE_DUPLICATE", (), strict_custom_fields=(("DEFAULT_UOM", "Default UOM"),),
    )
    alias = evaluate(
        "FAN MOTOR 2HP", "FAN MOTOR 2HP", context=strict,
        left={"DEFAULT_UOM": "PCS"}, right={"DEFAULT_UOM": "EA"},
    )
    assert alias.edge_class == IdentityEdgeClass.STRONG_SUPPORT

    different = evaluate(
        "FAN MOTOR 2HP", "FAN MOTOR 2HP", context=strict,
        left={"DEFAULT_UOM": "PCS"}, right={"DEFAULT_UOM": "BOX"},
    )
    assert different.edge_class == IdentityEdgeClass.NON_GROUPABLE
    assert different.classification_reason_codes == ("REQUEST_CONDITION_SCOPE_ONLY",)


def test_condition_values_compare_uom_aliases_and_ignore_missing_values():
    assert not condition_values_differ({"DEFAULT_UOM": "PCS"}, {"DEFAULT_UOM": "EA"}, "DEFAULT_UOM")
    assert condition_values_differ({"DEFAULT_UOM": "PCS"}, {"DEFAULT_UOM": "KG"}, "DEFAULT_UOM")
    assert not condition_values_differ({"DEFAULT_UOM": "PCS"}, {}, "DEFAULT_UOM")
    assert condition_values_differ({"GRADE": "A"}, {"GRADE": "b"}, "GRADE")


def test_field_group_constraint_rejects_any_two_known_different_values():
    constraint = (field_group_constraint("grade"),)
    assert constraint == ("FIELD:GRADE",)
    a, b, missing = {"GRADE": "A"}, {"GRADE": "B"}, {}
    # The missing record cannot bridge two known different values.
    assert not group_satisfies_request_constraints((missing, a, b), constraint)
    assert group_satisfies_request_constraints((missing, a, {"GRADE": "a"}), constraint)


def test_ambiguous_ownership_defers_only_the_unresolved_members():
    strong, review = IdentityEdgeClass.STRONG_SUPPORT, IdentityEdgeClass.REVIEW_SUPPORT
    non, cannot = IdentityEdgeClass.NON_GROUPABLE, IdentityEdgeClass.CANNOT_LINK
    edges = [
        edge(1, 2, strong), edge(3, 4, strong), edge(3, 5, strong), edge(4, 5, cannot),
        edge(2, 3, review), edge(1, 3, non), edge(1, 4, non), edge(1, 5, non),
        edge(2, 4, non), edge(2, 5, non),
    ]
    value = resolver_input([record(index) for index in range(1, 6)], edges)
    result = resolve_identity_groups(value, FakeTargetedProvider())
    # {1,2} is in every best partition; 3 pairs equally with 4 or 5.
    assert memberships(result) == ((1, 2),)
    assert [item.record_ids for item in result.deferred_work_units] == [(3, 4, 5)]


def test_disagreeing_identifying_numbers_are_not_positive_support():
    different = evaluate("LINKAGE ALPHA MODEL 5355387", "LINKAGE ALPHA BETA MODEL 6053553")
    assert different.edge_class == IdentityEdgeClass.NON_GROUPABLE
    assert different.classification_reason_codes == ("IDENTIFYING_NUMBERS_DISAGREE",)

    # Formatting differences of the same number still agree.
    for left, right in (("MCB 30A", "MCB30A"), ("BEARING 6205-2RS", "BEARING 6205 2RS")):
        assert evaluate(left, right).edge_class == IdentityEdgeClass.STRONG_SUPPORT


def test_garment_size_codes_separate_variants_without_reading_units_as_sizes():
    from app.engine.variant_extractor import extract_variant_attributes

    sizes = {
        "Nova jumpsuit black/stripe m": ["medium"],
        "Nova jumpsuit black/stripe xxl": ["extra extra large"],
        "1-pack 20 den tights black (9000) l": ["large"],
        "tights black onesize": ["one size"],
        "dress m/l": ["medium/large"],
        "Shirt size M blue": ["medium"],
        "Cable 5 m": [],
        "Oil 10 L": [],
        "Pipe clamp type S": [],
    }
    for description, expected in sizes.items():
        assert extract_variant_attributes(description)["SIZE"] == expected, description

    for left, right in (
        ("Nova jumpsuit black/stripe m", "Nova jumpsuit black/stripe xl"),
        ("Nova jumpsuit black/stripe s", "Nova jumpsuit black/stripe l"),
        ("1-pack 20 den tights black (9000) l", "1-pack 20 den tights black (9000) m"),
    ):
        relationship = evaluate(left, right)
        assert relationship.edge_class == IdentityEdgeClass.CANNOT_LINK
        assert relationship.classification_reason_codes == ("CRITICAL_MISMATCH_SIZE",)

    same = evaluate("Nova jumpsuit black/stripe m", "Nova jumpsuit black/stripe m")
    assert same.edge_class == IdentityEdgeClass.STRONG_SUPPORT
    unsized = evaluate("Nova jumpsuit black/stripe m", "Nova jumpsuit black/stripe")
    assert unsized.edge_class not in {
        IdentityEdgeClass.STRONG_SUPPORT, IdentityEdgeClass.REVIEW_SUPPORT,
    }
