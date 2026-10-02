"""Pure request-scoped compatibility rules for identity-group resolution.

A request-scoped condition (Site when selected, strict condition fields) says
which records may share a group in *this* scan. It is never stored as a pair
CANNOT_LINK, because the same two records may be grouped by a scan that does
not select the condition.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.engine.business_rules import condition_field_value
from app.engine.column_semantics import clean_field_value


CONTRACT_GROUP_CONSTRAINT = "CONTRACT"
REQUEST_SCOPED_GROUP_CONSTRAINTS = frozenset({CONTRACT_GROUP_CONSTRAINT})
FIELD_GROUP_CONSTRAINT_PREFIX = "FIELD:"


def field_group_constraint(field_key: str) -> str:
    return f"{FIELD_GROUP_CONSTRAINT_PREFIX}{str(field_key).strip().upper()}"


def is_allowlisted_group_constraint(constraint: str) -> bool:
    if constraint in REQUEST_SCOPED_GROUP_CONSTRAINTS:
        return True
    return bool(
        constraint.startswith(FIELD_GROUP_CONSTRAINT_PREFIX)
        and constraint[len(FIELD_GROUP_CONSTRAINT_PREFIX):].strip()
    )


def normalized_contract(value) -> str:
    """Normalize a contract for request-local comparison without persisting it."""
    return clean_field_value(value).casefold()


def record_contract(record) -> str:
    value = (
        record.get("CONTRACT")
        if isinstance(record, dict)
        else getattr(record, "contract", None)
    )
    return normalized_contract(value)


def contract_pair_is_compatible(left, right) -> bool:
    """Require equal known sites; reject known/missing; allow missing/missing."""
    left_contract = record_contract(left)
    right_contract = record_contract(right)
    if not left_contract and not right_contract:
        return True
    return bool(
        left_contract
        and right_contract
        and left_contract == right_contract
    )


def contract_group_is_compatible(records: Iterable) -> bool:
    records = tuple(records)
    if not records:
        return True
    first = records[0]
    return all(contract_pair_is_compatible(first, item) for item in records[1:])


def field_group_is_compatible(records: Iterable, field_key: str) -> bool:
    """Every recorded value in the group agrees (missing values are unknown)."""
    values = {condition_field_value(record, field_key) for record in records} - {""}
    return len(values) <= 1


def group_satisfies_request_constraints(records: Iterable, constraints) -> bool:
    records = tuple(records)
    for constraint in constraints:
        if constraint == CONTRACT_GROUP_CONSTRAINT:
            if not contract_group_is_compatible(records):
                return False
        elif constraint.startswith(FIELD_GROUP_CONSTRAINT_PREFIX):
            field_key = constraint[len(FIELD_GROUP_CONSTRAINT_PREFIX):]
            if not field_group_is_compatible(records, field_key):
                return False
    return True
