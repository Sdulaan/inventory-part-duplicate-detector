import pytest

from app.services.identity_group_presentation import (
    REQUIRES_HUMAN_REVIEW,
    human_review_presentation,
    system_candidate_label,
    system_evidence_tier,
)


@pytest.mark.parametrize(
    ("status", "tier"),
    [
        ("LIKELY_DUPLICATE_GROUP", "Stronger Evidence"),
        ("POSSIBLE_DUPLICATE_GROUP_REVIEW", "Review Evidence"),
    ],
)
def test_unreviewed_internal_statuses_map_to_advisory_presentation(status, tier):
    label = system_candidate_label(status)
    review_state, human_decision = human_review_presentation(None)

    assert label == "Potential Same-Identity Group"
    assert "confirmed duplicate" not in label.lower()
    assert system_evidence_tier(status) == tier
    assert review_state == REQUIRES_HUMAN_REVIEW
    assert human_decision == "Not yet reviewed"


@pytest.mark.parametrize(
    ("decision", "expected"),
    [
        ("CONFIRM_ALL_AS_ONE", "Human Confirmed Same-Identity Group"),
        ("CONFIRM_SELECTED", "Human Confirmed Same-Identity Group"),
        ("KEEP_ALL_SEPARATE", "Human Rejected Candidate"),
        ("UNSURE", "Review Deferred"),
    ],
)
def test_human_decision_is_the_display_authority(decision, expected):
    review_state, _ = human_review_presentation({
        "reviewed": True,
        "current_decision_type": decision,
    })

    assert review_state == expected
