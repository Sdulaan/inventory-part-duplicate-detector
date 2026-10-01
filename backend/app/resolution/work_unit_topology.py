"""Which records GF5 resolves together.

Only positive identity evidence connects records into a work unit: machine
STRONG_SUPPORT and REVIEW_SUPPORT edges and human MUST_LINK constraints.

STRONG_SUPPORT edges, MUST_LINK constraints and REVIEW_SUPPORT edges scoring
at least ``CONNECTING_REVIEW_SCORE`` always connect. Weaker review links are
then added strongest first, but only while the resulting unit stays within
``WEAK_LINK_MAX_UNIT_MEMBERS``. Look-alikes sharing only a "- Mit Pickup"
suffix are joined by hundreds of weak review links; added unconditionally they
chained whole product lines into units far over the member cap, which were
deferred and lost every duplicate inside them. Bounding weak links at the
member cap instead fills units to 20 records that then exceed the targeted
check budget. A small bound keeps isolated weak pairs and triples (often
abbreviation variants, "Gen oil fltr" / "Generator oil filter") while
stopping chains. A skipped link still counts as evidence for any pair that
ends up in the same unit. A unit over the member cap can only come from
connecting evidence and is deferred whole.

- A NON_GROUPABLE edge or a shared discovery neighbourhood only records that
  two records were compared; it says nothing about shared identity.
- A CANNOT_LINK edge or constraint restricts how a unit may be grouped; it
  never joins two units.

Letting comparisons join units chained unrelated families into components of
hundreds or thousands of records, far over the member cap, which were then
deferred whole and dropped every duplicate inside them.

The resolver and the result validator both derive units here, so the
validator reconstructs exactly the units the resolver worked on.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from app.engine.identity_edge import IdentityEdgeClass
from app.resolution.contracts import (
    IdentityResolutionConstraintType,
    IdentityResolutionInput,
)


# Measured on a 7,627-record customer file: records in over-cap units fell
# from 1,966 (every review link connecting) to 24, and grouped pairs of an
# earlier reviewed scan rose from 94 to 177 of 335.
CONNECTING_REVIEW_SCORE = 80.0
WEAK_LINK_MAX_UNIT_MEMBERS = 4


@dataclass(frozen=True)
class WorkUnitTopology:
    member_ids: tuple[int, ...]
    neighborhood_references: tuple[str, ...]
    truncated: bool
    degraded: bool
    reference: str


def work_unit_reference(neighborhood_references, member_ids) -> str:
    return (
        "|".join(neighborhood_references)
        or f"records:{','.join(map(str, member_ids))}"
    )


def positive_work_units(value: IdentityResolutionInput) -> tuple[WorkUnitTopology, ...]:
    parent = {record.record_id: record.record_id for record in value.canonical_records}

    def find(record_id: int) -> int:
        while parent[record_id] != record_id:
            parent[record_id] = parent[parent[record_id]]
            record_id = parent[record_id]
        return record_id

    size = {record_id: 1 for record_id in parent}

    def union(left: int, right: int, *, cap: int | None = None) -> None:
        first, second = find(left), find(right)
        if first == second:
            return
        if cap is not None and size[first] + size[second] > cap:
            return
        low, high = sorted((first, second))
        parent[high] = low
        size[low] += size[high]
        active.update((left, right))

    active: set[int] = set()
    review = []
    for edge in value.machine_evidence_edges:
        if edge.edge_class == IdentityEdgeClass.STRONG_SUPPORT or (
            edge.edge_class == IdentityEdgeClass.REVIEW_SUPPORT
            # Edges without a persisted score (legacy inputs) keep connecting.
            and (edge.deterministic_score is None
                 or edge.deterministic_score >= CONNECTING_REVIEW_SCORE)
        ):
            union(edge.record_id_1, edge.record_id_2)
        elif edge.edge_class == IdentityEdgeClass.REVIEW_SUPPORT:
            review.append(edge)
    for constraint in value.human_constraints:
        if constraint.constraint_type == IdentityResolutionConstraintType.MUST_LINK:
            union(constraint.record_id_1, constraint.record_id_2)
    # Strongest first; ties by scan-independent record references.
    references_by_id = {
        record.record_id: record.record_ref_key for record in value.canonical_records
    }
    review.sort(key=lambda edge: (
        -edge.deterministic_score,
        references_by_id[edge.record_id_1], references_by_id[edge.record_id_2],
    ))
    cap = min(WEAK_LINK_MAX_UNIT_MEMBERS, value.resolver_configuration.max_resolution_members)
    for edge in review:
        union(edge.record_id_1, edge.record_id_2, cap=cap)

    components: dict[int, list[int]] = {}
    for member in sorted(active):
        components.setdefault(find(member), []).append(member)

    # Every neighbourhood touching a unit is kept as its discovery provenance.
    # A neighbourhood is truncated when its anchor had more candidates than it
    # kept, so only the unit holding the anchor may be missing a member;
    # without an anchor every unit it touches is treated as affected.
    references: dict[int, set[str]] = {}
    truncated: set[int] = set()
    degraded: set[int] = set()
    for neighborhood in value.identity_neighborhoods:
        touched = {
            find(member) for member in neighborhood.member_record_ids if member in active
        }
        for root in touched:
            references.setdefault(root, set()).add(neighborhood.neighborhood_reference)
        anchor = neighborhood.anchor_record_id
        if anchor is not None:
            affected = {find(anchor)} if anchor in active else set()
        else:
            affected = touched
        if neighborhood.truncated:
            truncated.update(affected)
        if neighborhood.degraded:
            degraded.update(affected)

    units = []
    for root, members in components.items():
        neighborhood_refs = tuple(sorted(references.get(root, ())))
        units.append(WorkUnitTopology(
            member_ids=tuple(members),
            neighborhood_references=neighborhood_refs,
            truncated=root in truncated,
            degraded=root in degraded,
            reference=work_unit_reference(neighborhood_refs, members),
        ))
    # Units sharing every neighbourhood would share a reference; the lowest
    # member keeps such references unique and deterministic.
    counts: dict[str, int] = {}
    for unit in units:
        counts[unit.reference] = counts.get(unit.reference, 0) + 1
    return tuple(
        replace(unit, reference=f"{unit.reference}#{unit.member_ids[0]}")
        if counts[unit.reference] > 1 else unit
        for unit in units
    )
