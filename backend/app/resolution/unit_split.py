"""Deterministic split of work units too large to resolve as a whole.

A work unit is every record connected by any discovery link, so a family of
look-alike descriptions can chain into one unit of hundreds of records. Units
over ``max_resolution_members`` used to be deferred whole, dropping even the
obvious duplicates inside them.

An accepted group is always connected by positive (STRONG/REVIEW support)
evidence: group validation rejects neutral gaps in a group that is not
positively connected. So a unit is first split into its positive components,
which cannot separate any acceptable group. Components still too large are
split further by dropping the weakest positive links first; that step can
separate records that belong together, and whatever still exceeds the cap
stays deferred.

The resolver and the result validator both call this function, so each piece
is a work unit the validator can reconstruct from the same immutable input.
"""

from __future__ import annotations

from typing import Mapping

from app.engine.identity_edge import IdentityEdgeClass

_STRONG = IdentityEdgeClass.STRONG_SUPPORT
_REVIEW = IdentityEdgeClass.REVIEW_SUPPORT

# Positive links kept at each successive level, strongest last to be dropped.
_LEVELS = (
    lambda edge_class, generic: edge_class in (_STRONG, _REVIEW),
    lambda edge_class, generic: edge_class == _STRONG or (edge_class == _REVIEW and not generic),
    lambda edge_class, generic: edge_class == _STRONG,
    lambda edge_class, generic: edge_class == _STRONG and not generic,
)

SPLIT_REFERENCE_SEPARATOR = "#split:"


def split_reference(parent_reference: str, piece: tuple[int, ...]) -> str:
    """Work-unit reference of a piece; pieces are disjoint, so the first id is unique."""
    return f"{parent_reference}{SPLIT_REFERENCE_SEPARATOR}{piece[0]}"


def _components(members: tuple[int, ...], edges, keep) -> list[tuple[int, ...]]:
    parent = {member: member for member in members}

    def find(member):
        root = member
        while parent[root] != root:
            root = parent[root]
        while parent[member] != root:
            parent[member], member = root, parent[member]
        return root

    for (left, right), (edge_class, generic) in edges:
        if keep(edge_class, generic):
            first, second = find(left), find(right)
            if first != second:
                low, high = sorted((first, second))
                parent[high] = low
    grouped: dict[int, list[int]] = {}
    for member in members:
        grouped.setdefault(find(member), []).append(member)
    return [tuple(sorted(items)) for items in grouped.values() if len(items) >= 2]


def split_oversized_unit(
    member_ids: tuple[int, ...],
    lookup: Mapping[tuple[int, int], tuple[IdentityEdgeClass, bool]],
    max_members: int,
) -> tuple[tuple[tuple[int, ...], ...], tuple[tuple[int, ...], ...]]:
    """Return ``(pieces, still_oversized)`` for a unit over ``max_members``.

    Records with no positive link inside the unit belong to no piece; they
    could not be accepted in any group of this unit.
    """
    member_set = set(member_ids)
    edges = sorted(
        (pair, evidence) for pair, evidence in lookup.items()
        if pair[0] in member_set and pair[1] in member_set
    )
    pieces, oversized = [], []
    pending = [(tuple(sorted(member_ids)), 0)]
    while pending:
        members, level = pending.pop()
        inside = set(members)
        local_edges = [
            item for item in edges if item[0][0] in inside and item[0][1] in inside
        ]
        for component in _components(members, local_edges, _LEVELS[level]):
            if len(component) <= max_members:
                pieces.append(component)
            elif level + 1 < len(_LEVELS):
                pending.append((component, level + 1))
            else:
                oversized.append(component)
    return tuple(sorted(pieces)), tuple(sorted(oversized))
