# Request-scoped Site constraint

## Status

`REQUEST_SCOPED_SITE_CONSTRAINT_VERIFIED`

Site (`CONTRACT`) is now a hard final-group equality condition only when it is
present in the request's existing `selected_fields`. This is a request policy,
not a claim that records at different sites can never describe the same
physical identity.

## Semantic boundary

Previously, selecting Site affected standard candidate blocking and the shared
20% selected-field evidence score. Group-First hybrid retrieval could still
propose cross-site relationships, GF4 could classify them as Review support,
and GF5 could accept a multi-site review group. That behavior explains the
historical 158-group acceptance result and its five-site `CG-000010` example.

The corrected behavior is:

| Request | Candidate and group behavior |
|---|---|
| `CONTRACT` selected | Cross-site pairs are pruned from hybrid retrieval where possible, and GF5 rejects every candidate group that does not satisfy normalized Site equality. |
| `CONTRACT` unselected | No new Site restriction applies. Cross-site proposals, Review support, and GF5 groups remain eligible under the existing deterministic evidence rules. |

Standard selected-field scoring is unchanged. A matching selected Site still
contributes its existing positive evidence; the 20% business component was not
reweighted. `UNIT_MEAS` and every other checkbox retain their existing
discovery-and-scoring semantics and were not generalized into hard constraints.

## Missing values

Site comparison uses the existing cleaned field convention followed by
case-folding. Null, blank, whitespace-only, and existing missing-value markers
therefore normalize to missing.

- equal known values are compatible;
- different known values are incompatible;
- a known value and a missing value are incompatible; and
- two missing values remain compatible under the existing missing/missing
  convention.

This keeps a selected Site conservative without inventing a durable identity
rule. It also fails a group containing a mixture of known and missing Sites.

## Pipeline integration

Layer A is an efficiency boundary in `HybridCandidateRetriever`: when Site is
selected, cross-Site and known/missing pairs are excluded before hybrid
materialization. The standard blocking channel already partitions on selected
Site equality.

Layer B is authoritative. `IdentityResolutionInput` carries the canonical,
allowlisted tuple `request_scoped_group_constraints`. The persisted scan's
selected fields populate it for that resolution only. GF5 checks the entire
candidate membership before `_build_group` can accept it, and output validation
independently rejects a violating accepted group. The frozen GF5 objective
`(covered, likely_members, strong, -review, -group_count)`, traversal, bounds,
and deterministic ordering are unchanged over valid partitions.

The request constraint is included in the resolution input fingerprint. Engine
identifiers are now `identity-discovery-v7-request-scoped-site`,
`identity-discovery-config-v7`, and
`constrained-identity-resolver-v3-request-scoped-site`.

## GF4, persistence, and review authority

GF4's relationship ontology is unchanged. Site mismatch is not persisted as a
`CANNOT_LINK`, is not written to human-review constraints, and does not affect a
later scan where Site is unselected. Sequential same-database tests prove that
the second request can again form a cross-site group and that no
`IdentityResolutionConstraintInput` row is created by the request policy.

All output remains advisory. Eligible groups still require Confirm, Reject, or
Defer human review; this change does not auto-confirm or auto-merge anything.

## UI contract

The Duplicate-checking conditions screen identifies Site as **Must match when
selected**. Every other exposed field is described as **Used for candidate
discovery and scoring**. The mode help also states that Site is not enforced
when its checkbox is unselected. The API remains unchanged: `selected_fields`
is the single source of truth and no redundant strict-Site flag was added.

## 5,327-record acceptance

The safe canonical database snapshot for historical scan 34 was replayed in a
disposable SQLite database with Group-First authority, threshold 75, local
deterministic retrieval, and provider calls disabled. The protected workbook
was not accessed.

| Metric | Site + UOM selected | UOM selected, Site unselected |
|---|---:|---:|
| Records | 5,327 | 5,327 |
| S1 proposals / GF4 evidence edges | 20,381 | 20,492 |
| Final G2-v2 groups | 208 | 42 |
| Final group members | 436 | 94 |
| Cross-site final groups | **0** | **18** |
| Stronger Evidence groups | 82 | 12 |
| Review Evidence groups | 126 | 30 |
| Conflicts | 32 | 6 |
| Deferred | 32 | 6 |
| Unassigned | 4,891 | 5,233 |
| Targeted requests | 74 | 27 |
| Candidate partitions explored | 204,231 | 10,095 |
| Persisted request-derived human constraints | 0 | 0 |
| Provider calls | 0 | 0 |

Selected-Site request fingerprint:
`fab4c9e6de6bad086bd14b4582d16b9ad64ecb2330b7663f2cf7cab5fff3faff`.
The unselected-Site request fingerprint is
`6742e55aeecdd734e7e37875abbcf79f8c8ec8a1531d4c06bca6f3ebed49a85a`;
it has distinct downstream S1-S10
fingerprints while both runs share the same S0 fingerprint
`8107a36194f3bab4209a1f714fc7412a76288b11b2a7b93d536a9c20b55d6257`.

The exported workbook retained the five-sheet contract (`Overview`, `Review
Groups`, `Group Index`, `Detailed Data`, `Technical Reference`), contained 436
Detailed Data member rows, and contained zero groups with multiple known Sites.

Artifacts:

- `artifacts/request_scoped_site_constraint/acceptance_comparison.json`
- `artifacts/request_scoped_site_constraint/site_selected.acceptance_provenance.json`
- `artifacts/request_scoped_site_constraint/site_unselected.acceptance_provenance.json`

## Historical labeling

The 158-group artifact remains valid evidence of the old implementation and is
now labeled `PRE_SITE_HARD_CONSTRAINT_BASELINE`. It is historical-only, was not
rewritten, and is not an expected count for the corrected semantics.
