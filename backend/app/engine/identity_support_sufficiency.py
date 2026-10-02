"""Whether agreeing evidence actually identifies an item, separate from its score.

Match strength says how much of the comparable evidence agrees. This module
says whether that evidence is identity-discriminating enough for machine
STRONG_SUPPORT. Two identical descriptions such as "INDUSTRIAL COMPONENT"
agree 100% yet name only a category, so the pair stays REVIEW_SUPPORT.

The policy can only reduce STRONG_SUPPORT to REVIEW_SUPPORT; it never creates
support or a contradiction. Fuzzy part-number similarity is deliberately
absent: duplicate masters carry different part numbers by definition. Only
the same reference written with different punctuation counts.

STRONG_SUPPORT is kept when the pair shares either
  * independent corroboration: an identifying number or model code, a typed
    attribute (rating, dimension, type/grade), a physical measurement, an
    explicitly selected discriminating business field, or the same part
    reference written differently; or
  * at least ``MIN_SHARED_INFORMATIVE_TOKENS`` informative description words,
    i.e. words that are not category nouns, generic qualifiers, role/position
    words, stopwords or units.

Each source token is counted once, so signals derived from the same phrase
cannot corroborate each other.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.engine.column_semantics import clean_field_value
from app.engine.normalizer import normalize_description


IDENTITY_SUPPORT_SUFFICIENCY_VERSION = "identity-support-sufficiency-v1"
LOW_INFORMATION_REVIEW_REASON = "LOW_INFORMATION_IDENTITY_REQUIRES_REVIEW"
IDENTIFYING_NUMBERS_DISAGREE_REASON = "IDENTIFYING_NUMBERS_DISAGREE"
MIN_SHARED_INFORMATIVE_TOKENS = 2

_REFERENCE_PATH = (
    Path(__file__).resolve().parents[1]
    / "reference_data" / "non_discriminating_terms.v1.json"
)
_ROLE_KEYS = (
    "END_POSITION", "SERIALIZATION_ROLE", "FLOW_ROLE",
    "ENGINE_COMPONENT_ROLE", "STRUCTURAL_ROLE", "HIERARCHY",
)
_TYPED_KEYS = ("ELECTRICAL_RATING", "DIMENSION", "TYPE_OR_GRADE")
_PHYSICAL_KEYS = ("measurements", "dimensions")
# Site, UOM and workflow type say where or how an item is stocked, and the
# canonical classification codes (commodity, accounting group, product
# category/family, HSN/SAC, hazard) name a category shared by many items.
# Their equality never corroborates item identity, just as category wording
# does not. Other selected fields (e.g. a manufacturer part number) can.
_CONTEXT_FIELDS = frozenset({
    "CONTRACT", "UNIT_MEAS", "TYPE_CODE",
    "PRIME_COMMODITY", "SECOND_COMMODITY", "ACCOUNTING_GROUP",
    "PART_PRODUCT_CODE", "PART_PRODUCT_FAMILY", "PRODUCT_CATEGORY_ID",
    "HSN_SAC_CODE", "HAZARD_CODE",
})


def _load_reference(path: Path = _REFERENCE_PATH):
    raw = path.read_text(encoding="utf-8")
    payload = json.loads(raw)
    if payload.get("schema_version") != 1:
        raise RuntimeError("unsupported non-discriminating terms schema")
    terms = frozenset(
        str(term).casefold()
        for section in ("category_nouns", "qualifiers", "stopwords")
        for term in payload[section]
    )
    fingerprint = hashlib.sha256(json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    return payload["reference_version"], terms, fingerprint


(
    NON_DISCRIMINATING_TERMS_VERSION,
    NON_DISCRIMINATING_TERMS,
    NON_DISCRIMINATING_TERMS_FINGERPRINT,
) = _load_reference()


def same_part_reference(features_left, features_right) -> bool:
    """The same part reference written differently (BRG-6205-A vs BRG6205A).

    This is exact equality after removing punctuation, spacing and case, not
    similarity: PUMP-10001 and PUMP-10002 are different references.
    """
    left = re.sub(r"[^a-z0-9]", "", features_left.normalized_part_no.casefold())
    right = re.sub(r"[^a-z0-9]", "", features_right.normalized_part_no.casefold())
    return bool(left and left == right)


def _is_identifying_number(token: str) -> bool:
    """Model codes (2RS, M10, MCB30A) and multi-digit numbers (6205).

    A lone digit ("2") is too common to identify an item on its own.
    """
    if not re.search(r"\d", token):
        return False
    if re.search(r"[a-z]", token):
        return len(token) >= 2
    return len(re.sub(r"\D", "", token)) >= 3


def _role_tokens(features) -> set[str]:
    return {
        token
        for key in _ROLE_KEYS
        for value in features.variant_mapping().get(key, ())
        for token in normalize_description(value).split()
    }


def _record_tokens(row, features):
    uninformative = (
        NON_DISCRIMINATING_TERMS
        | _role_tokens(features)
        | set(normalize_description(row.get("UNIT_MEAS")).split())
    )
    tokens = features.normalized_description.split()
    informative = {
        token for token in tokens
        if token.isalpha() and len(token) >= 3 and token not in uninformative
    }
    identifying = {token for token in tokens if _is_identifying_number(token)}
    identifying |= {
        re.sub(r"[^a-z0-9]", "", model) for model in features.model_tokens
    } - {""}
    return informative, identifying


def _digit_runs(identifying: set[str]) -> set[str]:
    """Multi-digit runs inside identifying tokens: MCB30A and 30A both give 30."""
    return {
        run.lstrip("0") or "0"
        for token in identifying
        for run in re.findall(r"\d{2,}", token)
    }


@dataclass(frozen=True)
class IdentitySupportAssessment:
    shared_informative_tokens: tuple[str, ...]
    shared_identifying_numbers: tuple[str, ...]
    shared_typed_attributes: dict
    shared_physical: dict
    selected_discriminating_fields: tuple[str, ...]
    same_part_reference: bool = False
    # Both descriptions carry identifying numbers and no multi-digit run is
    # shared (MODEL 5355387 vs MODEL 6053553). Such a pair is not positive
    # identity support however similar the surrounding words are.
    identifying_numbers_disagree: bool = False

    @property
    def independent_corroboration(self) -> bool:
        return bool(
            self.same_part_reference
            or self.shared_identifying_numbers
            or any(self.shared_typed_attributes.values())
            or any(self.shared_physical.values())
            or self.selected_discriminating_fields
        )

    @property
    def sufficient_for_strong(self) -> bool:
        return self.independent_corroboration or (
            len(self.shared_informative_tokens) >= MIN_SHARED_INFORMATIVE_TOKENS
        )

    def payload(self) -> dict:
        return {
            "version": IDENTITY_SUPPORT_SUFFICIENCY_VERSION,
            "terms_reference_version": NON_DISCRIMINATING_TERMS_VERSION,
            "shared_informative_tokens": list(self.shared_informative_tokens),
            "shared_identifying_numbers": list(self.shared_identifying_numbers),
            "shared_typed_attributes": self.shared_typed_attributes,
            "shared_physical": self.shared_physical,
            "selected_discriminating_fields": list(self.selected_discriminating_fields),
            "same_part_reference": self.same_part_reference,
            "identifying_numbers_disagree": self.identifying_numbers_disagree,
            "independent_corroboration": self.independent_corroboration,
            "sufficient_for_strong": self.sufficient_for_strong,
        }


def assess_identity_support(
    left, right, features_left, features_right, selected_fields,
) -> IdentitySupportAssessment:
    informative_l, identifying_l = _record_tokens(left, features_left)
    informative_r, identifying_r = _record_tokens(right, features_right)
    typed = {
        key: sorted(
            set(features_left.variant_mapping().get(key, ()))
            & set(features_right.variant_mapping().get(key, ()))
        ) for key in _TYPED_KEYS
    }
    physical = {
        key: sorted(
            set(features_left.technical_mapping().get(key, ()))
            & set(features_right.technical_mapping().get(key, ()))
        ) for key in _PHYSICAL_KEYS
    }
    business = tuple(sorted({
        str(field).upper() for field in selected_fields
        if str(field).upper() not in _CONTEXT_FIELDS
        and clean_field_value(left.get(field))
        and clean_field_value(left.get(field)).casefold()
        == clean_field_value(right.get(field)).casefold()
    }))
    return IdentitySupportAssessment(
        shared_informative_tokens=tuple(sorted(informative_l & informative_r)),
        shared_identifying_numbers=tuple(sorted(identifying_l & identifying_r)),
        shared_typed_attributes=typed,
        shared_physical=physical,
        selected_discriminating_fields=business,
        same_part_reference=same_part_reference(features_left, features_right),
        identifying_numbers_disagree=bool(
            _digit_runs(identifying_l) and _digit_runs(identifying_r)
            and not _digit_runs(identifying_l) & _digit_runs(identifying_r)
        ),
    )
