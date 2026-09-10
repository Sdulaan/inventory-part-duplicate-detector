# R18I holdout Likely-group defect causal diagnostic

Classification: `R18I_NO_SAFE_GENERAL_CAUSE_PROVEN`

Next: `NEW_HUMAN_EVIDENCE_FOR_UNRESOLVED_CAUSE`

## Baseline, scope, and governance

R18I began from R18G-C commit
`0fe6f5578b148a4d347cce109425502c6c1e9822` on `llm-assisted-mvp`.
The protected `deterministic-demo-v1` tag remained at
`d510cf3c18b3a8448d0f79be3e59c398efb32eae`. This is a diagnostic-only
analysis: production runtime, GF4, GF5, GF6, persistence, API, UI, export,
threshold, and provider behavior are unchanged. Provider calls were 0.

The 16-group holdout is now `CONSUMED_FOR_DIAGNOSTIC_USE`. Its labels and
comments may support diagnosis, but it is permanently ineligible as an
independent future validation set. `POST_R18_CORRECTION_INDEPENDENT_VALIDATION_REQUIRED
= YES`: any later runtime correction requires a new independently sampled and
human-labelled group holdout before demo-quality graduation can be claimed.

## Result

All six rejected Likely groups and both accepted Likely controls are
two-member, one-edge groups. Every edge is `STRONG_SUPPORT`; every group has
complete pairwise coverage, density 1.0, no Review edge, no R18C downgrade, no
cannot-link, no missing pair, and no unresolved bridge. Therefore the immediate
mechanical cause is a false-positive Strong edge in each rejected pair, not a
GF5 choice among competing partitions. Current GF6 Likely promotion faithfully
applies its all-internal-pairs-Strong rule.

The consumed evidence does not isolate a safe general deterministic boundary.
Five failures are lexical-only or unresolved, but both accepted holdout
controls and five of six Development SAME Likely controls have the same
provenance. The remaining failed case contains trusted identity evidence and
depends on external business convention. A blanket trusted-path status gate
would therefore damage every accepted holdout control and most Development
positive controls while still retaining one rejected group.

## Six rejected Likely groups

All Senior judgments below have `MEDIUM` confidence. Full visible source fields,
member references, current group IDs, evidence JSON, score components, and the
unredacted comments are preserved in the ignored R18I audit artifacts.

| Review group | Members (site: part number — description) | Reason / basis | Senior comment | Primary diagnosis | Input actionability |
|---|---|---|---|---|---|
| `R18G-00AF18329702C143` | DES13: NAS-REPL2 — NAS REPL2; DES13: NAS-REPL1 — NAS REPL2 | `DIFFERENT_MODEL_TYPE_OR_VARIANT` / `UNCLEAR` | Part numbers explicitly differ (NAS-REPL1 vs NAS-REPL2), indicating separate sequential replacement parts; NAS-REPL1's description matching 'NAS REPL2' looks like a copy-paste error or This might be true duplicate or different product. More like for duplicate | `STATUS_PROMOTION_ERROR` | `MIXED_OR_UNCLEAR` |
| `R18G-2F16563526EE4262` | IFT91: JD-SERIAL-2 — Condition code enabled; IFT91: JD-SERIAL — Condition code enabled | `DOMAIN_KNOWLEDGE_REQUIRED` / `DOMAIN_EXTERNAL` | Both share the flag-like description 'Condition code enabled' and same site/type; the '-2' suffix on JD-SERIAL-2 may denote a specific serialized instance rather than a distinct catalog item, but confirming that needs this business's serial-tracking convention, which isn't visible here. | `DATA_INSUFFICIENCY_OR_EXTERNAL_KNOWLEDGE` | `PARTIALLY_ACTIONABLE` |
| `R18G-5490F834A64C724D` | SH D: MT-ENG S1 — Mitsubishi Lancer 200 car engine mount; SH D: MT-ENG S2 — same description | `DIFFERENT_CRITICAL_ATTRIBUTE` / `DOMAIN_EXTERNAL` | Identical generic description ('Mitsubishi Lancer 200 car engine mount'), but the S1/S2 suffixes likely denote different mounting positions (e.g. left/right or front/rear mount) for the same vehicle model. | `DATA_INSUFFICIENCY_OR_EXTERNAL_KNOWLEDGE` | `PARTIALLY_ACTIONABLE` |
| `R18G-CC0A28A5B2EDB984` | PC61: HP-FIFO — FIRST IN FIRST OUT; PC61: HP-FIFO-02 — same description | `GENERIC_OR_COPIED_TEXT_NOT_ENOUGH` / `UNCLEAR` | Both share the generic placeholder description 'FIRST IN FIRST OUT'; HP-FIFO-02's explicit '-02' suffix suggests a separate numbered test record in a FIFO test series rather than a duplicate of HP-FIFO. | `STATUS_PROMOTION_ERROR` | `MIXED_OR_UNCLEAR` |
| `R18G-D455182FD8423849` | DSITE: YINPPART2 — Testing Purposes; DSITE: YINPPART — same description | `GENERIC_OR_COPIED_TEXT_NOT_ENOUGH` / `UNCLEAR` | Both share the placeholder description 'Testing Purposes'; YINPPART2's explicit '2' suffix indicates a separate sequential test record from YINPPART rather than a duplicate. | `STATUS_PROMOTION_ERROR` | `MIXED_OR_UNCLEAR` |
| `R18G-FCF98461F3E7F6F3` | PC62: RDEW IP5 — RDEW IP1; PC62: RDEW IP1 — RDEW IP1 | `DIFFERENT_MODEL_TYPE_OR_VARIANT` / `UNCLEAR` | RDEW IP5 and RDEW IP1 are explicitly different sequence numbers; RDEW IP5's matching 'RDEW IP1' description looks like a copy-paste error rather than evidence of a duplicate. | `STATUS_PROMOTION_ERROR` | `MIXED_OR_UNCLEAR` |

The four `UNCLEAR` cases remain `MIXED_OR_UNCLEAR`; the diagnostic does not
silently reinterpret them as source-visible. The two `DOMAIN_EXTERNAL` cases
have visible unresolved suffixes, so they are only partially actionable; their
claimed meaning is not deterministically established by the available fields.

## Pair topology and promotion trace

| Review group | Score | Evidence provenance | Unresolved observations | GF4 / topology | R18C downgrade |
|---|---:|---|---:|---|---|
| `R18G-00AF18329702C143` | 98.75 | lexical-only/unresolved | 3 | Strong / `ALL_STRONG` | none |
| `R18G-2F16563526EE4262` | 94.41 | trusted identity present | 4 | Strong / `ALL_STRONG` | none |
| `R18G-5490F834A64C724D` | 98.57 | lexical-only/unresolved | 6 | Strong / `ALL_STRONG` | none |
| `R18G-CC0A28A5B2EDB984` | 93.57 | lexical-only/unresolved | 5 | Strong / `ALL_STRONG` | none |
| `R18G-D455182FD8423849` | 94.41 | lexical-only/unresolved | 3 | Strong / `ALL_STRONG` | none |
| `R18G-FCF98461F3E7F6F3` | 98.57 | lexical-only/unresolved | 3 | Strong / `ALL_STRONG` | none |

For each pair the evaluator emitted `DETERMINISTIC_LIKELY_DUPLICATE` and
`ALLOW`, with no protected conflict. The exact deterministic path is:

1. GF4 emits one Strong edge for the two members.
2. The only non-singleton candidate contains that edge; no competing eligible
   two-member partition can separate the members except leaving them uncovered.
3. GF5 selects objective `(2, 2, 1, 0, -1)`—two covered records, two Likely
   members, one Strong edge, zero Review edges, and one group.
4. Complete pairwise validation sees 1/1 Strong, zero Review/cannot-link/missing
   evidence, and no bridge.
5. GF6 assigns `LIKELY_DUPLICATE_GROUP` because Strong count equals possible
   internal pair count.

Under a more cautious interpretation, all six memberships could remain Review
hypotheses, but the tested evidence does not justify a boundary that separates
them from positive controls. Accordingly, the four lexical failures are
diagnosed as status-promotion errors at case level, not as proof that a global
status-only correction is safe. The external cases are data/domain limitations.

## Accepted Likely controls and over-correction risk

| Review group | Members | Human result | Evidence |
|---|---|---|---|
| `R18G-2C4A9CE59FA3450B` | SD-M-BOARD / SD-M-BOARD2, identical “pcp board” description | SAME, Medium, `UNCLEAR` | Strong, score 94.41, lexical-only/unresolved, 3 unresolved observations |
| `R18G-3FAF9FCACBD97366` | AK TEST1 / AK KOMPONENT TEST1, identical “Test 1 AK” description | SAME, High, `DOMAIN_EXTERNAL` | Strong, score 96.09, lexical-only/unresolved, 3 unresolved observations |

| Feature | Rejected Likely | Accepted Likely | Generality and correction risk |
|---|---:|---:|---|
| all Strong / density 1 / weakest link Strong | 6/6 | 2/2 | no discrimination; maximum over-correction risk |
| description-dominant | 6/6 | 2/2 | no discrimination; maximum risk |
| trusted identity present | 1/6 | 0/2 | inverse of a safe rejection signal |
| lexical-only or unresolved | 5/6 | 2/2 | catches most failures but all holdout controls |
| unresolved discriminator present | 6/6 | 2/2 | no discrimination |
| part-number coherence floor met | 6/6 | 2/2 | no discrimination |
| group size two | 6/6 | 2/2 | no discrimination |
| native or R18C Review edge | 0/6 | 0/2 | absent everywhere |

The apparent trailing-number pattern is also present in the accepted board
control. Treating suffixes, exact nouns, descriptions, group IDs, or part
numbers as fitted rejection rules would be unsafe and is prohibited.

## GF5 causal assessment

Classification: `GF5_NOT_PRIMARY_CAUSE`.

Each rejected group has two members and one eligible Strong pair. There was no
alternative generated group over the same two records that the objective could
prefer. The objective chose coverage over the empty/singleton result exactly as
designed; it did not choose a risky coarsening among competing partitions.
R18H therefore remains frozen and `GF5-GROUP-PARTITION-RESIDUAL-MIXING` is not
reclassified from this evidence.

## Shadow Likely policies

| Policy | Rejected retained | Accepted controls retained | Development SAME Likely retained | Finding |
|---|---:|---:|---:|---|
| S1 all internal pairs Strong | 6/6 | 2/2 | 6/6 | identical to current facts |
| S2 minimum Strong density (observed density 1.0) | 6/6 | 2/2 | 6/6 | no separation |
| S3 any Review remains Review | 6/6 | 2/2 | 6/6 | no Review edge exists |
| S4 weakest-link Strong | 6/6 | 2/2 | 6/6 | identical to current facts |
| S5 trusted path per member | 1/6 | 0/2 | 1/6 | harms all holdout and 5/6 Development positive controls, yet misses one failure |

All counterfactuals are monotonic shadow-only status downgrades. None changed
runtime or membership. S1–S4 are ineffective and S5 is unsafe. Therefore a
status-only correction is **not safe** on current evidence. Bicycle generic
deferral, Head/Tail cannot-link behavior, R18C invariants, and Review semantics
remain unchanged; the 3 human-rejected Review groups do not justify global
Review suppression.

## Interpretation and decision

All six failures are `SEMANTIC_INTERPRETATION_GAP` candidates for possible
future shadow advisory: four involve ambiguous sequence/copy semantics and two
explicitly require external conventions. This does not authorize an LLM call,
runtime authority, a Group Confidence Index, Identity Context Projection, or
XLSX-vNext. Binary status may be insufficient for communicating cohesive but
description-dominant or unresolved groups, but R19A remains unauthorized.

Primary classification is `R18I_NO_SAFE_GENERAL_CAUSE_PROVEN`. Secondary
finding: pair/evidence classification is mechanically over-permissive for these
six cases, but current human evidence cannot identify a bounded feature that
corrects it without breaking known positives. `NEXT =
NEW_HUMAN_EVIDENCE_FOR_UNRESOLVED_CAUSE`; no R18J correction is implemented.
The first-class identity-set principle remains unchanged: same-site duplicate
conditions and cross-site related records are downstream contextual views only.

## Deterministic evidence and tests

Ignored artifacts under `artifacts/gf12_a2_human_identity_review/`:

- `r18i_failed_likely_group_audit.csv`
- `r18i_group_pair_topology.csv`
- `r18i_likely_status_shadow_policies.csv`
- `r18i_summary.json`

The harness opens SQLite using `mode=ro`, selects the exact 6+2 cases, rebuilds
their active GF4 evidence, traces promotion, compares controls, and writes only
ignored analysis outputs. Focused tests cover exact selection, topology,
promotion, diagnosis, actionability, GF5 causality, shadow monotonicity, frozen
decision constants, and absence of mutating SQL. Runtime regression tests
verify no behavior change.
