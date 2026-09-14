"""Offline R18J-0 reconciliation of all existing Senior-reviewed Strong evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

from app.benchmarks.r18g_group_human_evidence import sha256_file, write_manifest
from app.benchmarks.r18i_holdout_likely_diagnostic import (
    STRONG,
    _canonical,
    _pair_diagnostic,
    _readonly,
)
from app.engine.identity_evidence_evaluator import DeterministicIdentityContext


CLASSIFICATION = "R18J_0_NO_SAFE_SOURCE_VISIBLE_DISCRIMINATOR"
NEXT = "DEMO_SAFE_PRODUCTIZATION_WITHOUT_ACCURACY_OVERCLAIM"
DEMO_CONTRACT = "ADVISORY_REQUIRES_HUMAN_REVIEW"
POST_CORRECTION_HOLDOUT_REQUIRED = "YES"
CONFIDENCE_ORDER = {"": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}
LABEL_MAP = {
    "SAME_IDENTITY": "SAME",
    "SAME_ONE_IDENTITY": "SAME",
    "DIFFERENT_IDENTITY": "DIFFERENT",
    "NOT_ONE_IDENTITY": "DIFFERENT",
    "INSUFFICIENT_INFORMATION": "INSUFFICIENT",
}
TOKEN_RE = re.compile(r"[a-z]+|\d+", re.IGNORECASE)


class R18J0DiagnosticError(ValueError):
    """Fail-closed invalid or irreconcilable human evidence."""


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def canonical_pair_fingerprint(left_ref: str, right_ref: str) -> str:
    refs = sorted((left_ref, right_ref))
    payload = "r18j0-canonical-pair-v1\0" + "\0".join(refs)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _unique_join(values) -> str:
    return " || ".join(sorted({str(value).strip() for value in values if str(value).strip()}))


def reconcile_observations(observations: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for observation in observations:
        grouped[str(observation["canonical_pair_fingerprint"])].append(observation)
    reconciled = []
    for fingerprint in sorted(grouped):
        values = grouped[fingerprint]
        labels = {str(value["human_label"]) for value in values}
        preferred = max(
            values,
            key=lambda value: (
                int(value.get("evidence_precedence", 0)),
                CONFIDENCE_ORDER.get(str(value.get("human_confidence", "")), 0),
                str(value["review_pair_id"]),
            ),
        )
        merged = dict(preferred)
        merged.update({
            "review_source": _unique_join(value["review_source"] for value in values),
            "review_pair_id": _unique_join(value["review_pair_id"] for value in values),
            "human_reason": _unique_join(value.get("human_reason", "") for value in values),
            "human_comment": _unique_join(value.get("human_comment", "") for value in values),
            "comment_basis": _unique_join(value.get("comment_basis", "") for value in values),
            "human_label": (
                next(iter(labels)) if len(labels) == 1 else "CONFLICTING_HUMAN_LABELS"
            ),
            "human_label_observations": _unique_join(
                value["human_label"] for value in values
            ),
            "observation_count": len(values),
        })
        reconciled.append(merged)
    return reconciled


def source_visibility_class(row: dict[str, object]) -> str:
    if row["human_label"] != "DIFFERENT":
        return "NOT_APPLICABLE"
    basis = str(row.get("comment_basis", ""))
    if "DOMAIN_EXTERNAL" in basis:
        return "EXTERNAL_KNOWLEDGE_DOMINANT"
    if bool(row.get("protected_conflict")) or bool(row.get("technical_attribute_conflict")):
        return "SOURCE_VISIBLE_ACTIONABLE"
    assessment = row.get("assessment", {}) or {}
    if assessment.get("requires_strong_downgrade"):
        return "SOURCE_VISIBLE_ACTIONABLE"
    if (
        row.get("part_number_residual_divergence")
        or row.get("generic_copied_description_dominance")
        or row.get("model_type_conflict")
    ) and str(row.get("human_comment", "")).strip():
        return "PARTIALLY_ACTIONABLE"
    return "UNRESOLVED"


def _json(value, fallback):
    if not value:
        return fallback
    return json.loads(value)


def _norm(value) -> str:
    return " ".join(TOKEN_RE.findall(str(value or "").lower()))


def _tokens(value) -> set[str]:
    return set(TOKEN_RE.findall(str(value or "").lower()))


def _variant_values(technical: dict) -> tuple[dict, dict]:
    return technical.get("variant_attributes_1", {}), technical.get("variant_attributes_2", {})


def _has_disjoint_variant(left: dict, right: dict) -> bool:
    for key in sorted(set(left) | set(right)):
        a, b = set(left.get(key) or []), set(right.get(key) or [])
        if a and b and a.isdisjoint(b):
            return True
    return False


def derive_features(source_a: dict, source_b: dict, assessment: dict, technical: dict) -> dict[str, object]:
    part_a, part_b = _norm(source_a.get("part_no")), _norm(source_b.get("part_no"))
    desc_a, desc_b = _norm(source_a.get("description")), _norm(source_b.get("description"))
    residual = _tokens(part_a) ^ _tokens(part_b)
    numeric_a = {token for token in _tokens(part_a) if token.isdigit()}
    numeric_b = {token for token in _tokens(part_b) if token.isdigit()}
    alpha_a = {token for token in _tokens(part_a) if token.isalpha()}
    alpha_b = {token for token in _tokens(part_b) if token.isalpha()}
    discriminator = technical.get("identity_discriminator") or {}
    variants_a, variants_b = _variant_values(technical)
    rec_a, rec_b = discriminator.get("record_1") or {}, discriminator.get("record_2") or {}
    class_a, class_b = rec_a.get("resolved_object_class"), rec_b.get("resolved_object_class")
    type_a, type_b = set(variants_a.get("TYPE_OR_GRADE") or []), set(variants_b.get("TYPE_OR_GRADE") or [])
    fields = (
        "part_no", "description", "uom", "type_code", "prime_commodity",
        "second_commodity", "accounting_group", "part_product_code",
        "part_product_family", "product_category_id", "hsn_sac_code", "hazard_code",
    )
    filled_a = sum(source_a.get(field) not in (None, "") for field in fields)
    filled_b = sum(source_b.get(field) not in (None, "") for field in fields)
    protected = int(discriminator.get("protected_conflict_count") or 0) > 0
    variant_conflict = _has_disjoint_variant(variants_a, variants_b)
    return {
        "same_part_type": _norm(source_a.get("type_code")) == _norm(source_b.get("type_code")),
        "same_uom": _norm(source_a.get("uom")) == _norm(source_b.get("uom")),
        "same_site": _norm(source_a.get("contract")) == _norm(source_b.get("contract")),
        "exact_normalized_description": bool(desc_a and desc_a == desc_b),
        "exact_normalized_part_number": bool(part_a and part_a == part_b),
        "part_number_residual_divergence": bool(residual),
        "part_number_residual_tokens": sorted(residual),
        "numeric_residual_divergence": numeric_a != numeric_b,
        "alphabetic_residual_divergence": alpha_a != alpha_b,
        "independent_non_description_support_missing": not bool(
            assessment.get("independent_identity_support_present")
        ),
        "unresolved_residual_divergence": int(
            assessment.get("unresolved_discriminator_count") or 0
        ) > 0,
        "generic_copied_description_dominance": bool(
            assessment.get("generic_or_copy_risk")
            or (assessment.get("description_dominance") and desc_a == desc_b)
        ),
        "description_only_evidence": bool(
            assessment.get("description_dominance")
            and not assessment.get("cross_field_identity_anchor_present")
        ),
        "identity_signature_incomplete": min(filled_a, filled_b) <= 4,
        "identity_filled_fields_a": filled_a,
        "identity_filled_fields_b": filled_b,
        "protected_conflict": protected,
        "technical_attribute_conflict": variant_conflict,
        "variant_agreement": "CONFLICT" if variant_conflict else "NO_OBSERVED_CONFLICT",
        "object_function_class_agreement": (
            "AGREE" if class_a and class_a == class_b
            else "CONFLICT" if class_a and class_b and class_a != class_b
            else "UNRESOLVED"
        ),
        "object_function_conflict": bool(class_a and class_b and class_a != class_b),
        "model_type_agreement": (
            "AGREE" if type_a and type_a == type_b
            else "CONFLICT" if type_a and type_b and type_a.isdisjoint(type_b)
            else "UNRESOLVED"
        ),
        "model_type_conflict": bool(type_a and type_b and type_a.isdisjoint(type_b)),
        "critical_attribute_agreement": (
            "CONFLICT" if protected or variant_conflict else "NO_OBSERVED_CONFLICT"
        ),
    }


def _source_payload(row) -> dict[str, object]:
    return {
        key: row[key] for key in (
            "source_row_index", "part_no", "description", "contract", "uom",
            "type_code", "prime_commodity", "second_commodity", "accounting_group",
            "part_product_code", "part_product_family", "product_category_id",
            "hsn_sac_code", "hazard_code", "normalized_part_no",
            "normalized_description",
        )
    }


def _observation(*, review_source, review_pair_id, left_ref, right_ref, human_label,
                 confidence, reason, comment, basis, source_a, source_b, pair,
                 group_context="PAIR_REVIEW", current_status="", precedence=1):
    assessment = pair.get("lexical_trust_assessment") or {}
    technical = pair.get("technical_evidence") or {}
    features = derive_features(source_a, source_b, assessment, technical)
    scores = pair.get("score_components") or {}
    fingerprint = canonical_pair_fingerprint(left_ref, right_ref)
    return {
        "review_source": review_source,
        "review_pair_id": review_pair_id,
        "canonical_pair_fingerprint": fingerprint,
        "left_member_reference": left_ref,
        "right_member_reference": right_ref,
        "human_label": LABEL_MAP.get(human_label, human_label),
        "human_confidence": confidence,
        "human_reason": reason,
        "human_comment": comment,
        "comment_basis": basis,
        "part_numbers": json.dumps([source_a.get("part_no") or "", source_b.get("part_no") or ""]),
        "descriptions": json.dumps([source_a.get("description") or "", source_b.get("description") or ""]),
        "master_descriptions": json.dumps(["", ""]),
        "type_designations": json.dumps([source_a.get("type_code") or "", source_b.get("type_code") or ""]),
        "dimension_quality": json.dumps(["", ""]),
        "uoms": json.dumps([source_a.get("uom") or "", source_b.get("uom") or ""]),
        "part_types": json.dumps([source_a.get("type_code") or "", source_b.get("type_code") or ""]),
        "sites": json.dumps([source_a.get("contract") or "", source_b.get("contract") or ""]),
        "gf4_class": STRONG,
        "provenance": assessment.get("support_provenance") or pair.get("support_provenance", ""),
        "lexical_trust_assessment_json": json.dumps(assessment, sort_keys=True),
        "r18c_state": "POST_R18C_RETAINED_STRONG",
        "description_similarity": scores.get("description_similarity", ""),
        "part_number_similarity": scores.get("part_no_similarity", ""),
        "tfidf_score": scores.get("tfidf_score", ""),
        "fuzzy_score": scores.get("fuzzy_score", ""),
        "technical_token_agreement": scores.get("technical_token_score", ""),
        "variant_agreement": features["variant_agreement"],
        "object_function_class_agreement": features["object_function_class_agreement"],
        "model_type_agreement": features["model_type_agreement"],
        "critical_attribute_agreement": features["critical_attribute_agreement"],
        "unresolved_residual_tokens": assessment.get("unresolved_discriminator_count", ""),
        "part_number_residual_tokens_json": json.dumps(features["part_number_residual_tokens"]),
        "identity_signature_completeness": (
            f"{features['identity_filled_fields_a']}/12|{features['identity_filled_fields_b']}/12"
        ),
        "generic_copied_text_state": str(features["generic_copied_description_dominance"]).lower(),
        "same_part_type": str(features["same_part_type"]).lower(),
        "same_uom": str(features["same_uom"]).lower(),
        "same_site": str(features["same_site"]).lower(),
        "group_topology_context": group_context,
        "current_status": current_status,
        "classification_reason_codes_json": json.dumps(pair.get("classification_reason_codes") or []),
        "technical_evidence_json": json.dumps(technical, sort_keys=True),
        "source_a_json": json.dumps(source_a, sort_keys=True),
        "source_b_json": json.dumps(source_b, sort_keys=True),
        "assessment": assessment,
        "evidence_precedence": precedence,
        **features,
    }


def _r18_observations(shadow_path, reference_path, mapping_path):
    references = {row["review_pair_id"]: row for row in read_csv(reference_path)}
    mappings = {row["review_pair_id"]: row for row in read_csv(mapping_path)}
    shadows = read_csv(shadow_path)
    if set(references) != set(mappings) or {row["review_pair_id"] for row in shadows} != set(mappings):
        raise R18J0DiagnosticError("R18J0_R18_SOURCE_RECONCILIATION_FAILED")
    observations = []
    for row in shadows:
        if row["shadow_corrected_edge_class"] != STRONG:
            continue
        pair_id = row["review_pair_id"]
        mapping, human = mappings[pair_id], references[pair_id]
        source_a = _json(row["record_a_source_fields_json"], {})
        source_b = _json(row["record_b_source_fields_json"], {})
        pair = {
            "score_components": _json(row["component_scores_json"], {}),
            "technical_evidence": _json(row["technical_evidence_json"], {}),
            "lexical_trust_assessment": _json(row["lexical_trust_assessment_json"], {}),
            "classification_reason_codes": _json(row["current_classification_reason_codes_json"], []),
            "support_provenance": row["frozen_shadow_bucket"],
        }
        sources = ["R18_PAIR_REFERENCE"]
        if "EVALUATION" in row["panel_membership"].split("|"):
            sources.append("R18_300_PAIR_EVALUATION_PANEL")
        observations.append(_observation(
            review_source="|".join(sources), review_pair_id=pair_id,
            left_ref=mapping["record_a_stable_ref"], right_ref=mapping["record_b_stable_ref"],
            human_label=human["identity_label"], confidence=human["confidence"],
            reason=human["reason_code"], comment=human["reviewer_comment"], basis="",
            source_a=source_a, source_b=source_b, pair=pair, precedence=1,
        ))
    return observations


def _database_pair(connection, context, refs):
    records, source = [], []
    for ref in refs:
        row = connection.execute(
            "SELECT * FROM scan_record_snapshot WHERE scan_id=31 AND record_ref_key=?",
            (ref,),
        ).fetchone()
        if row is None:
            raise R18J0DiagnosticError(f"R18J0_SOURCE_RECORD_UNAVAILABLE:{ref}")
        records.append(_canonical(row))
        source.append(_source_payload(row))
    pair = _pair_diagnostic(records[0], records[1], context)
    return source[0], source[1], pair


def _group_observations(path, review_source, connection, context, precedence):
    observations = []
    for row in read_csv(path):
        if int(row["member_count"]) != 2:
            continue
        label = LABEL_MAP.get(row["normalized_group_label"])
        if not label:
            continue
        refs = row["source_member_refs"].split("|")
        source_a, source_b, pair = _database_pair(connection, context, refs)
        if pair["edge_class"] != STRONG:
            continue
        observations.append(_observation(
            review_source=review_source, review_pair_id=row["review_group_id"],
            left_ref=refs[0], right_ref=refs[1], human_label=row["normalized_group_label"],
            confidence=row["confidence"], reason=row["reason_code"],
            comment=row["reviewer_comment"], basis=row["comment_basis"],
            source_a=source_a, source_b=source_b, pair=pair,
            group_context=f"TWO_MEMBER_ONE_EDGE|{row.get('source_kind', '')}",
            current_status=row.get("system_status", ""), precedence=precedence,
        ))
    return observations


def _targeted_observations(partition_path, mapping_path, development_path, connection, context):
    partitions = read_csv(partition_path)
    mappings = {row["review_group_id"]: row for row in read_csv(mapping_path)}
    development = {row["review_group_id"]: row for row in read_csv(development_path)}
    by_group = defaultdict(list)
    for row in partitions:
        by_group[row["review_group_id"]].append(row)
    observations = []
    for group_id in sorted(by_group):
        mapping, human = mappings[group_id], development[group_id]
        refs = mapping["source_member_refs"].split("|")
        partition_by_member = {
            int(row["member_no"]): row["canonical_human_partition"]
            for row in by_group[group_id]
        }
        if len(refs) != len(partition_by_member):
            raise R18J0DiagnosticError("R18J0_TARGETED_PARTITION_RECONCILIATION_FAILED")
        for left_index, right_index in combinations(range(len(refs)), 2):
            pair_refs = (refs[left_index], refs[right_index])
            source_a, source_b, pair = _database_pair(connection, context, pair_refs)
            if pair["edge_class"] != STRONG:
                continue
            same = partition_by_member[left_index + 1] == partition_by_member[right_index + 1]
            observations.append(_observation(
                review_source="R18G_TARGETED_PARTITION_REVIEW",
                review_pair_id=f"{group_id}:M{left_index + 1}-M{right_index + 1}",
                left_ref=pair_refs[0], right_ref=pair_refs[1],
                human_label="SAME_IDENTITY" if same else "DIFFERENT_IDENTITY",
                confidence=human["confidence"], reason=human["reason_code"],
                comment=human["reviewer_comment"], basis=human["comment_basis"],
                source_a=source_a, source_b=source_b, pair=pair,
                group_context="TARGETED_HUMAN_PARTITION_PAIR",
                current_status=human.get("system_status", ""), precedence=4,
            ))
    return observations


def _r18i_observations(audit_path, topology_path, connection, context):
    topology = {row["review_group_id"]: row for row in read_csv(topology_path)}
    observations = []
    for row in read_csv(audit_path):
        refs = row["member_references"].split("|")
        source_a, source_b, pair = _database_pair(connection, context, refs)
        if pair["edge_class"] != STRONG or row["review_group_id"] not in topology:
            raise R18J0DiagnosticError("R18J0_R18I_RECONCILIATION_FAILED")
        human_label = "DIFFERENT_IDENTITY" if row["case_role"] == "FAILED_LIKELY" else "SAME_IDENTITY"
        observations.append(_observation(
            review_source="R18I_DIAGNOSTIC_REASSESSMENT",
            review_pair_id=row["review_group_id"], left_ref=refs[0], right_ref=refs[1],
            human_label=human_label, confidence=row["senior_confidence"],
            reason=row["senior_reason_code"], comment=row["senior_reviewer_comment"],
            basis=row["senior_comment_basis"], source_a=source_a, source_b=source_b,
            pair=pair, group_context=row["topology_class"],
            current_status="LIKELY_DUPLICATE_GROUP", precedence=5,
        ))
    return observations


RULES = {
    "PART_TYPE_CONFLICT": lambda row: row["same_part_type"] == "false",
    "UOM_CONFLICT": lambda row: row["same_uom"] == "false",
    "TECHNICAL_ATTRIBUTE_CONFLICT": lambda row: bool(row["technical_attribute_conflict"]),
    "MODEL_TYPE_CONFLICT": lambda row: bool(row["model_type_conflict"]),
    "OBJECT_FUNCTION_CONFLICT": lambda row: bool(row["object_function_conflict"]),
    "INDEPENDENT_NON_DESCRIPTION_SUPPORT_MISSING": lambda row: bool(row["independent_non_description_support_missing"]),
    "PART_NUMBER_RESIDUAL_DIVERGENCE": lambda row: bool(row["part_number_residual_divergence"]),
    "NUMERIC_RESIDUAL_DIVERGENCE": lambda row: bool(row["numeric_residual_divergence"]),
    "ALPHABETIC_RESIDUAL_DIVERGENCE": lambda row: bool(row["alphabetic_residual_divergence"]),
    "UNRESOLVED_RESIDUAL_DIVERGENCE": lambda row: bool(row["unresolved_residual_divergence"]),
    "GENERIC_COPIED_DESCRIPTION_DOMINANCE": lambda row: bool(row["generic_copied_description_dominance"]),
    "DESCRIPTION_ONLY_EVIDENCE": lambda row: bool(row["description_only_evidence"]),
    "IDENTITY_SIGNATURE_INCOMPLETE": lambda row: bool(row["identity_signature_incomplete"]),
    "LEXICAL_UNRESOLVED_WEAKEST_PATH": lambda row: row["provenance"] == "SHADOW_LEXICAL_ONLY_OR_UNRESOLVED",
    "CROSS_SITE_ONLY_SUPPORT": lambda row: row["same_site"] == "false",
    "EXACT_DESCRIPTION_AND_PART_RESIDUAL": lambda row: bool(row["exact_normalized_description"] and row["part_number_residual_divergence"]),
    "DESCRIPTION_DOMINANT_AND_NUMERIC_RESIDUAL": lambda row: bool(row["generic_copied_description_dominance"] and row["numeric_residual_divergence"]),
    "LEXICAL_UNRESOLVED_AND_PART_RESIDUAL": lambda row: bool(row["provenance"] == "SHADOW_LEXICAL_ONLY_OR_UNRESOLVED" and row["part_number_residual_divergence"]),
}


def evidence_family(row):
    sources = str(row["review_source"])
    if "HOLDOUT" in sources or "R18I" in sources:
        return "CONSUMED_HOLDOUT"
    if "TARGETED" in sources:
        return "DEVELOPMENT_TARGETED"
    if "DEVELOPMENT" in sources:
        return "DEVELOPMENT_GROUP"
    return "R18_PAIR"


def classify_rule(*, different_caught, same_harmed, caught_families, source_visible_caught):
    if different_caught == 0:
        return "NOT_ACTIONABLE"
    if same_harmed:
        return "CONTRADICTED_BY_POSITIVE_CONTROLS"
    if caught_families == {"CONSUMED_HOLDOUT"}:
        return "OVERFIT_TO_CONSUMED_HOLDOUT"
    if different_caught >= 3 and len(caught_families) >= 2 and source_visible_caught >= 2:
        return "REPEATED_GENERAL_SIGNAL"
    return "PROMISING_BUT_TOO_SMALL"


def evaluate_rules(rows):
    labelled = [row for row in rows if row["human_label"] in {"SAME", "DIFFERENT"}]
    output = []
    for name, predicate in RULES.items():
        selected = [row for row in labelled if predicate(row)]
        caught = [row for row in selected if row["human_label"] == "DIFFERENT"]
        harmed = [row for row in selected if row["human_label"] == "SAME"]
        source_visible = [row for row in caught if row["source_visibility"] == "SOURCE_VISIBLE_ACTIONABLE"]
        families = {evidence_family(row) for row in caught}
        classification = classify_rule(
            different_caught=len(caught), same_harmed=len(harmed),
            caught_families=families, source_visible_caught=len(source_visible),
        )
        output.append({
            "candidate_rule": name,
            "evidence_classification": classification,
            "human_different_strong_caught": len(caught),
            "human_different_strong_total": sum(row["human_label"] == "DIFFERENT" for row in labelled),
            "human_same_strong_harmed": len(harmed),
            "human_same_strong_total": sum(row["human_label"] == "SAME" for row in labelled),
            "caught_high_confidence": sum(row["human_confidence"] == "HIGH" for row in caught),
            "caught_medium_confidence": sum(row["human_confidence"] == "MEDIUM" for row in caught),
            "caught_low_confidence": sum(row["human_confidence"] == "LOW" for row in caught),
            "development_different_caught": sum(row["human_label"] == "DIFFERENT" and evidence_family(row).startswith("DEVELOPMENT") for row in selected),
            "development_different_total": sum(row["human_label"] == "DIFFERENT" and evidence_family(row).startswith("DEVELOPMENT") for row in labelled),
            "development_same_harmed": sum(row["human_label"] == "SAME" and evidence_family(row).startswith("DEVELOPMENT") for row in selected),
            "development_same_total": sum(row["human_label"] == "SAME" and evidence_family(row).startswith("DEVELOPMENT") for row in labelled),
            "holdout_different_caught": sum(row["human_label"] == "DIFFERENT" and evidence_family(row) == "CONSUMED_HOLDOUT" for row in selected),
            "holdout_different_total": sum(row["human_label"] == "DIFFERENT" and evidence_family(row) == "CONSUMED_HOLDOUT" for row in labelled),
            "holdout_same_harmed": sum(row["human_label"] == "SAME" and evidence_family(row) == "CONSUMED_HOLDOUT" for row in selected),
            "holdout_same_total": sum(row["human_label"] == "SAME" and evidence_family(row) == "CONSUMED_HOLDOUT" for row in labelled),
            "source_visible_different_caught": len(source_visible),
            "source_visible_different_total": sum(row["source_visibility"] == "SOURCE_VISIBLE_ACTIONABLE" for row in labelled),
            "supporting_case_count": len(selected),
            "supporting_evidence_families": "|".join(sorted(families)),
        })
    return output


def demo_decision(rule_rows):
    if any(row["evidence_classification"] == "REPEATED_GENERAL_SIGNAL" for row in rule_rows):
        return "R18J_0_SAFE_GENERAL_STRONG_TRUST_CORRECTION_FOUND", "R18K_BOUNDED_STRONG_TRUST_CORRECTION"
    if any(row["evidence_classification"] == "PROMISING_BUT_TOO_SMALL" for row in rule_rows):
        return "R18J_0_PROMISING_SIGNAL_REQUIRES_TINY_HUMAN_CHECK", "R18J_1_TINY_TARGETED_HUMAN_CHECK"
    return CLASSIFICATION, NEXT


def run_diagnostic(*, r18_shadow, r18_reference, r18_mapping, development,
                   targeted_partition, targeted_mapping, holdout, r18i_audit,
                   r18i_topology, database, output_dir):
    observations = _r18_observations(r18_shadow, r18_reference, r18_mapping)
    connection = _readonly(database)
    scan = connection.execute("SELECT selected_fields FROM duplicate_scan WHERE id=31").fetchone()
    if scan is None:
        raise R18J0DiagnosticError("R18J0_SCAN31_UNAVAILABLE")
    context = DeterministicIdentityContext("DISCOVERY", tuple(json.loads(scan["selected_fields"])))
    observations.extend(_group_observations(development, "R18G_DEVELOPMENT_GROUP_REVIEW", connection, context, 3))
    observations.extend(_targeted_observations(targeted_partition, targeted_mapping, development, connection, context))
    observations.extend(_group_observations(holdout, "R18G_CONSUMED_HOLDOUT_GROUP_REVIEW", connection, context, 4))
    observations.extend(_r18i_observations(r18i_audit, r18i_topology, connection, context))
    connection.close()
    reconciled = reconcile_observations(observations)
    for row in reconciled:
        row["source_visibility"] = source_visibility_class(row)
    rules = evaluate_rules(reconciled)
    classification, next_task = demo_decision(rules)
    if classification != CLASSIFICATION:
        raise R18J0DiagnosticError(f"R18J0_UNEXPECTED_CORRECTION_SIGNAL:{classification}")

    public_fields = tuple(key for key in reconciled[0] if key not in {
        "assessment", "evidence_precedence", "identity_filled_fields_a",
        "identity_filled_fields_b", "protected_conflict", "technical_attribute_conflict",
        "object_function_conflict", "model_type_conflict", "part_number_residual_tokens",
    })
    public_rows = [{key: row[key] for key in public_fields} for row in reconciled]
    impact = [{
        "candidate_rule": row["candidate_rule"],
        "known_same_strong_preserved": row["human_same_strong_total"] - row["human_same_strong_harmed"],
        "known_same_strong_total": row["human_same_strong_total"],
        "accepted_holdout_likely_harmed": row["holdout_same_harmed"],
        "development_same_harmed": row["development_same_harmed"],
        "bicycle_deferral": "UNCHANGED_ANALYSIS_ONLY",
        "head_tail_cannot_link": "UNCHANGED_ANALYSIS_ONLY",
        "r18c_positive_controls": "ACCOUNTED_IN_UNIFIED_SAME_STRONG",
        "runtime_change": "NONE",
    } for row in rules]

    output_dir.mkdir(parents=True, exist_ok=True)
    unified_path = output_dir / "r18j0_unified_strong_human_evidence.csv"
    rules_path = output_dir / "r18j0_candidate_discriminator_evaluation.csv"
    impact_path = output_dir / "r18j0_positive_control_impact.csv"
    summary_path = output_dir / "r18j0_summary.json"
    write_csv(unified_path, public_rows)
    write_csv(rules_path, rules)
    write_csv(impact_path, impact)
    labels = Counter(row["human_label"] for row in reconciled)
    visibility = Counter(
        row["source_visibility"] for row in reconciled if row["human_label"] == "DIFFERENT"
    )
    family_counts = Counter(evidence_family(row) for row in reconciled)
    summary = {
        "classification": classification,
        "next": next_task,
        "runtime_correction_authorized": False,
        "tiny_human_check_needed": False,
        "demo_contract": DEMO_CONTRACT,
        "demo_language": [
            "Potential Same-Identity Group",
            "System-Suggested Candidate Group",
            "Requires Human Review",
        ],
        "forbidden_demo_claims": [
            "LIKELY_DUPLICATE_GROUP_AS_CONFIRMED_TRUTH",
            "UNSUPPORTED_PRECISION_OR_ACCURACY",
            "UNDESIGNED_CONFIDENCE_PERCENTAGES",
        ],
        "xlsx_demo_posture": {
            "section_a": "HUMAN_REVIEWED_CONFIRMED_DECISIONS_IF_AVAILABLE",
            "section_b": "SYSTEM_SUGGESTED_CANDIDATE_GROUPS_REQUIRES_REVIEW",
            "section_c": "REJECTED_DEFERRED_CONFLICT_CONTEXT_WHERE_USEFUL",
            "implemented": False,
        },
        "human_evidence_governance": {
            "r18_pair_reference_judgments": 316,
            "r18_evaluation_panel_memberships": 300,
            "r18g_development_group_judgments": 48,
            "r18g_targeted_groups": 2,
            "r18g_targeted_member_assignments": 9,
            "r18g_consumed_holdout_group_judgments": 16,
            "r18i_failed_likely": 6,
            "r18i_accepted_likely_controls": 2,
            "claim_limit": "DEVELOPMENT_AND_CONSUMED_DIAGNOSTIC_EVIDENCE_NOT_PRODUCTION_TRUTH",
        },
        "raw_observation_count": len(observations),
        "canonical_strong_pair_count": len(reconciled),
        "canonical_label_counts": dict(sorted(labels.items())),
        "evidence_family_counts": dict(sorted(family_counts.items())),
        "different_source_visibility_counts": dict(sorted(visibility.items())),
        "candidate_rule_class_counts": dict(sorted(Counter(
            row["evidence_classification"] for row in rules
        ).items())),
        "best_source_visible_discriminators": [],
        "decision_reason": (
            "No candidate is a repeated source-visible signal with zero SAME-control harm; "
            "surviving Strong DIFFERENT cases are partial, unresolved, or external, and "
            "structural residual rules also select known SAME Strong controls"
        ),
        "r18i_status_error_reassessment": (
            "The four cases remain ambiguous from available fields and unsuitable for "
            "confident presentation; wider evidence contains SAME controls with the same "
            "description-dominant residual patterns"
        ),
        "r18i_external_case_reassessment": "INPUT_INFORMATION_LIMIT",
        "new_human_review_requested": False,
        "post_runtime_correction_independent_holdout_required": POST_CORRECTION_HOLDOUT_REQUIRED,
        "runtime_changes": 0,
        "gf5_policy": "FROZEN_UNCHANGED",
        "provider_calls": 0,
        "source_hashes": {
            path.name: sha256_file(path) for path in (
                r18_shadow, r18_reference, r18_mapping, development,
                targeted_partition, targeted_mapping, holdout, r18i_audit, r18i_topology,
            )
        },
    }
    summary["artifacts"] = {
        path.name: {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
        for path in (unified_path, rules_path, impact_path)
    }
    write_manifest(summary_path, summary)
    return {**summary, "summary_artifact": {"bytes": summary_path.stat().st_size, "sha256": sha256_file(summary_path)}}


def main():
    parser = argparse.ArgumentParser()
    for name in (
        "r18-shadow", "r18-reference", "r18-mapping", "development",
        "targeted-partition", "targeted-mapping", "holdout", "r18i-audit",
        "r18i-topology", "database", "output-dir",
    ):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    result = run_diagnostic(**{key.replace("-", "_"): value for key, value in vars(args).items()})
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
