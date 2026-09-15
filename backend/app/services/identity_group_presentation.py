"""Presentation-only labels for system candidates and human review authority."""

from __future__ import annotations


SYSTEM_CANDIDATE_LABEL = "Potential Same-Identity Group"
REQUIRES_HUMAN_REVIEW = "Requires Human Review"

_EVIDENCE_TIERS = {
    "LIKELY_DUPLICATE_GROUP": "Stronger Evidence",
    "POSSIBLE_DUPLICATE_GROUP_REVIEW": "Review Evidence",
}

_HUMAN_STATES = {
    "CONFIRM_ALL_AS_ONE": (
        "Human Confirmed Same-Identity Group",
        "Confirmed all records as one identity",
    ),
    "CONFIRM_SELECTED": (
        "Human Confirmed Same-Identity Group",
        "Confirmed selected records as one identity",
    ),
    "SPLIT_PARTITIONS": (
        "Human Reviewed - Split into Identity Sets",
        "Split into separate identity sets",
    ),
    "KEEP_ALL_SEPARATE": (
        "Human Rejected Candidate",
        "Rejected and kept separate",
    ),
    "UNSURE": (
        "Review Deferred",
        "Deferred for later review",
    ),
}


def system_candidate_label(_status: str) -> str:
    """Never translate an unreviewed internal status into a truth claim."""
    return SYSTEM_CANDIDATE_LABEL


def system_evidence_tier(status: str) -> str:
    return _EVIDENCE_TIERS.get(status, "Unspecified Evidence")


def human_review_presentation(state: dict | None) -> tuple[str, str]:
    if not state or not state.get("reviewed"):
        return REQUIRES_HUMAN_REVIEW, "Not yet reviewed"
    return _HUMAN_STATES.get(
        state.get("current_decision_type"),
        ("Human Review Recorded", "Human decision recorded"),
    )
