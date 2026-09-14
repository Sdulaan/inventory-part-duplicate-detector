# Independent review: repeated-scan determinism correction

## Classification

`DETERMINISM_FIX_APPROVED_WITH_NONBLOCKING_FINDINGS`

Reviewed commit: `2fd786a5f89e7233dbfeeda33fe3a6515f7200dd`

Parent: `a7c9bbf589e94dd22118388f0e9a4893cc136489`

Provider calls: **0**

There are no blocking findings. The commit is a bounded determinism correction.
It changes which objectively tied or cap-bound candidates survive, and it makes
both cold and warm vector scoring use the existing persisted precision. It does
not change GF4 classification policy, the GF5 objective, human authority,
cannot-link enforcement, XLSX behavior, or provider execution.

## Findings

### LOW-1: the acceptance JSON is not self-provenancing

Evidence: `three_scan_acceptance.json` records three distinct scan IDs, cache
states, runtimes, one shared S0-S10 fingerprint table, counts, and zero provider
calls. It does not record the Git commit, input fingerprint, configuration
fingerprint, engine/reference-data versions, or a separate stage table for each
run.

Affected artifact: `artifacts/determinism_cache_and_gf5_ordering/three_scan_acceptance.json`.

Why it matters: the JSON alone cannot prove which executable revision and
configuration produced it or demonstrate per-run equality without relying on
the producer's shared-table representation.

Blocking: **no**. An independent fresh full scan at the reviewed commit matched
every committed stage count and fingerprint exactly.

Smallest correction: in the next diagnostics-only artifact revision, add commit,
input/configuration/version fingerprints and per-run S0-S10 results. Do not
change runtime behavior for this finding.

### LOW-2: two summary documents omit the complete qualification in place

Evidence: `PROJECT_SSOT.md` and `docs/CURRENT_PROJECT_ASSESSMENT.md` correctly
describe the three-run result and link to the fully qualified correction report,
but their opening summaries do not state all four bounds together: same input,
same engine version, same configuration, and same deterministic reference data.
The correction report and final demo checklist do state the complete scope.

Affected documentation: `PROJECT_SSOT.md` and
`docs/CURRENT_PROJECT_ASSESSMENT.md` opening determinism sections.

Why it matters: a reader who stops at either summary could overgeneralize the
claim to row-order, configuration, reference-data, or cross-version invariance.

Blocking: **no**. Runtime behavior and the detailed authoritative qualification
are correct.

Smallest correction: repeat the exact four-part qualification in both summary
sections during the next documentation maintenance task.

### OBSERVATION-1: seven-decimal canonicalization is a bounded semantic change

The correction does not preserve the parent's cold-cache scoring semantics.
Both fresh and cached vectors now enter the same seven-decimal representation
before L2 normalization and similarity scoring. This intentionally makes cold
behavior equal to the pre-existing persisted/warm representation.

On 384 seeded representative unit vectors (147,072 directed non-self scores),
the maximum observed cosine-score delta from the parent cold representation was
`2.980232238769531e-07`. There were zero strict ordering reversals across 72,960
tested top-20 pair-order relations. An intentionally constructed boundary probe
changed `+3.999999975690116e-08` to zero and therefore produced one crossing of
the character materialization gate `similarity > 0`; the corresponding negative
probe also became zero but did not cross that Boolean gate. Protected GF4,
Head/Tail, Bicycle, and R18C tests remained unchanged.

### OBSERVATION-2: retrieval identity is intentionally source-order-sensitive

`retrieval-order-key-v1` is SHA-256 over sorted compact canonical JSON containing
the lower-case canonical source-record fingerprint and zero-based source-row
ordinal. It contains no scan ID, database ID, UUID, timestamp, Python hash, or
unordered serialization. Equal-content rows at different ordinals remain
distinct; the same content and ordinal in another scan receives the same key.
The CSV/DataFrame ingestion path preserves input order and assigns
`range(len(source))`. Reordering source rows therefore intentionally changes
retrieval identities and is outside the repeatability claim.

## Runtime-file classification

| File | Classification | Purpose | Behavior changed | Authorized | Risk |
|---|---|---|---|---|---|
| `backend/app/services/canonical_record_service.py` | `RETRIEVAL_DETERMINISM` | Derive stable record/pair ordering keys | Yes | Yes | Low |
| `backend/app/services/character_retrieval.py` | `RETRIEVAL_DETERMINISM` | Stable LSH insertion, retention, and rerank ties | Yes | Yes | Medium |
| `backend/app/services/lexical_retrieval.py` | `RETRIEVAL_DETERMINISM` | Stable exact/bounded lexical ties | Yes | Yes | Medium |
| `backend/app/services/hybrid_retrieval.py` | `CACHE_REPRESENTATION_DETERMINISM`, `RETRIEVAL_DETERMINISM` | Align vector precision and all cap/tie ordering | Yes | Yes | High, tested |
| `backend/app/services/scan_runner.py` | `RETRIEVAL_DETERMINISM` | Supply semantic ordering keys while retaining record refs | Yes | Yes | Low |
| `backend/app/services/identity_discovery_service.py` | `RETRIEVAL_DETERMINISM` | Stable proposal order | Yes | Yes | Medium |
| `backend/app/services/identity_neighborhood_service.py` | `RETRIEVAL_DETERMINISM` | Stable anchor/member cap order | Yes | Yes | Medium |
| `backend/app/resolution/contracts.py` | `GF5_ORDERING_DETERMINISM` | Version the corrected resolver | Yes | Yes | Low |
| `backend/app/resolution/resolver.py` | `GF5_ORDERING_DETERMINISM` | Stable work units, requests, candidates, and partitions | Yes | Yes | High, tested |
| `backend/app/benchmarks/scan_determinism_audit.py` | `DIAGNOSTICS` | Normalize scan-local audit references semantically | Diagnostic only | Yes | Low |

No runtime file is classified `UNEXPECTED`.

## Cache assessment

Canonicalization occurs in `canonical_embedding_vector`: input is converted to
`float64`, rounded to seven decimal places, and converted to `float32`.
SQL and memory cache loads apply it; newly encoded miss vectors apply it before
cache save and before joining the scoring matrix; SQL storage serializes the
same seven-decimal values. Both paths are then stacked, L2-normalized, and sent
to exact or LSH/exact-rerank cosine scoring.

The change therefore alters both fresh and warm execution relative to their raw
inputs but makes them converge on the pre-existing persisted representation.
It can resolve sub-precision order differences or remove an essentially-zero
positive vector edge. This is bounded, documented, deterministic, and did not
change a protected GF4 outcome in the focused or real-data checks.

## Retrieval ordering assessment

Lexical exact/bounded selection, character LSH insertion/candidate retention and
exact rerank, channel pair materialization, exact/family/technical caps, tier and
global caps, proposal order, and neighborhood anchor/member selection all use
retrieval keys. Canonical `record_ref_key` values remain in persistence,
fingerprints, audit evidence, API references, and output identities.

No scan-local identifier remains as a meaningful retrieval decision tie-break.
`proposal_order` is consumed by neighborhood selection, but that value is now
itself assigned by semantic priority and retrieval pair key.

## GF5 assessment

The objective is unchanged and remains exactly:

```text
(covered, likely_members, strong, -review, -group_count)
```

Term definitions, direction, candidate eligibility, complete-pairwise checks,
cannot-link rejection, Strong/Review meaning, and the equal-best
stable-intersection/defer policy are unchanged. Semantic member tuples now order
work units, targeted checks, candidate traversal, and partition signatures.
The final semantic signature does not add a business preference: it identifies
objectively equal partitions reproducibly and preserves the existing ambiguity
handling. Remaining ID/ref sorts affect normalization, connectivity-only
traversal, persistence, or presentation—not the selected semantic partition.

## Parent-versus-corrected semantics

Historical Scan 34 is a comparable warm-cache parent execution and is diagnostic,
not ground truth. The independent corrected scan produced:

| Measure | Parent Scan 34 | Corrected | Delta |
|---|---:|---:|---:|
| S1 proposal pairs | 20,492 | 20,492 | 20,375 common; 117 replaced each way |
| S3 GF4 pairs | 20,492 | 20,492 | 20,375 common; 117 replaced each way |
| Common-pair GF4 class changes | 0 | 0 | None |
| GF5 groups | 158 | 158 | 128 common; 30 replaced each way |
| Stronger/Likely groups | 51 | 45 | -6 |
| Review groups | 107 | 113 | +6 |
| Conflicts | 28 | 27 | -1 |
| Deferred | 40 | 40 | 0 |
| Unassigned | 4,986 | 4,982 | -4 |

Among common S1 pairs, 20,371 proposal-order values and 383 non-order proposal
payloads changed because canonical channel ranks/caps changed. None of the
20,375 common GF4 pair payloads or classes changed. These real-data differences
are `EXPECTED_CANONICAL_TIE_RESOLUTION`. The numeric cold-path probe is the
separate bounded `CACHE_REPRESENTATION_EFFECT`. No
`UNEXPECTED_SEMANTIC_CHANGE` was found.

## Independent reproducibility evidence

A new isolated SQLite database was populated from the immutable canonical source
fields of historical Scan 34 in source-row order. One fresh 5,327-row Group-First
scan ran with LLM, group-provider, auto-triage, semantic enrichment, and recall
rescue execution disabled. It completed in `295.173 s`, made zero provider calls,
and matched every committed S0-S10 count and SHA-256 fingerprint exactly. It also
matched `171,251` candidate partition explorations and the 45/113 group split.

Focused replay independently covered cold then warm retrieval and same semantic
GF5 graph under different scan/database IDs. The focused review suite passed
137 tests, the wider safety/XLSX suite passed 226 tests, and each of
`PYTHONHASHSEED=1`, `2`, and `3` passed the seven determinism regression tests.
The earlier exact-tree full-suite evidence remains 1,865 passed and 15 skipped.

## Performance

Classification: `NO_MATERIAL_REGRESSION`.

The independent scan spent 51.084 s in discovery, 20.906 s in signed GF4
evidence, 216.395 s in GF5 resolution, and 295.173 s total. Parent Scan 34 used
43.964 s / 18.392 s / 190.216 s for those stages; parent Scan 35 used
57.527 s / 31.871 s / 203.575 s. The corrected independent result remains within
observed comparable run variability, while its GF5 time is also within the
committed corrected range of 201.246-222.121 s. No optimization is warranted by
this review.

## Safety and XLSX

The independent result contains zero accepted cannot-link violations and zero
duplicate accepted memberships. Focused coverage preserved human authority,
append-only review persistence, the frozen GF5 policy, R18C lexical safety,
Head/Tail directional protection, and Bicycle generic-evidence behavior.

The committed workbook opens with exactly `Overview`, `Review Groups`,
`Group Index`, `Detailed Data`, and `Technical Reference`. It has 158 group rows,
345 rows in each member-level sheet, 45 Stronger Evidence and 113 Review Evidence
groups, zero formulas, expected grouped-sheet merges, no flat-sheet merges, and
intact advisory and human-authoritative wording. XLSX runtime code was unchanged.

## Documentation and next gate

The fully supported claim is limited to the same input (including row order),
engine version, configuration, and deterministic reference data. It is not
row-order, configuration, reference-data, or cross-version invariance and is not
an accuracy or automatic-merge claim.

Further work is authorized subject to the existing governance boundaries.

```text
NEXT:
  hard-coded assumption audit
```

That audit should classify assumptions as `KEEP_IN_CODE`,
`MOVE_TO_SIMPLE_CONFIG`, `POSSIBLE_LLM_SEMANTIC_CASE`, or
`LEAVE_UNTIL_REAL_CLIENT_REQUIREMENT`. It must not introduce LLM behavior merely
because an assumption is identified.
