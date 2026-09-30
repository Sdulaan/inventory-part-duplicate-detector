"""Lookup tables derived once per immutable GF-5 resolution input.

Resolution visits every work unit and every candidate group of a scan. The
tables below depend only on the frozen input, so they are built on first use
and reused for that input object instead of being rebuilt for each visit.
"""

from __future__ import annotations

import weakref
from collections import ChainMap
from typing import Callable, Mapping

from app.engine.identity_edge import IdentityEdgeClass
from app.resolution.contracts import IdentityResolutionConstraintType

_TABLES: dict[int, tuple[weakref.ref, dict]] = {}


def _cached(value, name: str, build: Callable):
    key = id(value)
    entry = _TABLES.get(key)
    if entry is None or entry[0]() is not value:
        entry = (
            weakref.ref(value, lambda _ref, key=key: _TABLES.pop(key, None)),
            {},
        )
        _TABLES[key] = entry
    tables = entry[1]
    if name not in tables:
        tables[name] = build(value)
    return tables[name]


def record_references(value) -> dict[int, str]:
    return _cached(value, "references", lambda item: {
        record.record_id: record.record_ref_key for record in item.canonical_records
    })


def semantic_record_keys(value) -> dict[int, str]:
    return _cached(value, "semantic_keys", lambda item: {
        record.record_id: record.retrieval_order_key
        for record in item.canonical_records
    })


def record_ids(value) -> frozenset[int]:
    return _cached(value, "record_ids", lambda item: frozenset(
        record.record_id for record in item.canonical_records
    ))


def records_by_id(value) -> dict:
    return _cached(value, "records_by_id", lambda item: {
        record.record_id: record for record in item.canonical_records
    })


def neighborhood_references(value) -> frozenset[str]:
    return _cached(value, "neighborhood_references", lambda item: frozenset(
        neighborhood.neighborhood_reference
        for neighborhood in item.identity_neighborhoods
    ))


def machine_lookup(value) -> dict[tuple[int, int], tuple[IdentityEdgeClass, bool]]:
    return _cached(value, "machine_lookup", lambda item: {
        (edge.record_id_1, edge.record_id_2): (edge.edge_class, edge.generic_only)
        for edge in item.machine_evidence_edges
    })


def machine_edges_by_pair(value) -> dict:
    return _cached(value, "machine_edges", lambda item: {
        (edge.record_id_1, edge.record_id_2): edge
        for edge in item.machine_evidence_edges
    })


def human_cannot_links(value) -> dict:
    return _cached(value, "human_cannot_links", lambda item: {
        (constraint.record_id_1, constraint.record_id_2): constraint
        for constraint in item.human_constraints
        if constraint.constraint_type == IdentityResolutionConstraintType.CANNOT_LINK
    })


def _human_constraints_by_pair(value) -> dict[tuple[int, int], tuple]:
    def build(item):
        grouped: dict[tuple[int, int], list] = {}
        for constraint in item.human_constraints:
            pair = (constraint.record_id_1, constraint.record_id_2)
            grouped.setdefault(pair, []).append(constraint)
        return {pair: tuple(items) for pair, items in grouped.items()}
    return _cached(value, "human_by_pair", build)


def _apply_human_constraints(current, constraints):
    for constraint in constraints:
        if constraint.constraint_type == IdentityResolutionConstraintType.CANNOT_LINK:
            current = (IdentityEdgeClass.CANNOT_LINK, False)
        elif not current or current[0] != IdentityEdgeClass.CANNOT_LINK:
            current = (IdentityEdgeClass.STRONG_SUPPORT, False)
    return current


def _human_overlay(value) -> dict:
    def build(item):
        machine = machine_lookup(item)
        return {
            pair: _apply_human_constraints(machine.get(pair), constraints)
            for pair, constraints in _human_constraints_by_pair(item).items()
        }
    return _cached(value, "human_overlay", build)


def evidence_lookup(
    value, targeted_results=(),
) -> Mapping[tuple[int, int], tuple[IdentityEdgeClass, bool]]:
    """Machine evidence, then targeted results, then human constraints in order.

    Equivalent to copying the machine lookup and applying both layers, but
    only the pairs the layers touch are materialized per call.
    """
    overlay = {}
    for result in targeted_results:
        request = result.request
        overlay[(request.record_id_1, request.record_id_2)] = (
            result.edge_class, result.generic_only
        )
    human = _human_constraints_by_pair(value)
    for pair in [pair for pair in overlay if pair in human]:
        overlay[pair] = _apply_human_constraints(overlay[pair], human[pair])
    return ChainMap(overlay, _human_overlay(value), machine_lookup(value))
