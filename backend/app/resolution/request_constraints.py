"""Pure request-scoped compatibility rules for identity-group resolution."""

from __future__ import annotations

from collections.abc import Iterable

from app.engine.column_semantics import clean_field_value


CONTRACT_GROUP_CONSTRAINT = "CONTRACT"
REQUEST_SCOPED_GROUP_CONSTRAINTS = frozenset({CONTRACT_GROUP_CONSTRAINT})


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
